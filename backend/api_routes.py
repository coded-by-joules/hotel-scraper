from . import db
from . database import *
from flask import Blueprint, jsonify, request, send_file, Response
import subprocess
import pandas as pd
from io import BytesIO
from urllib.parse import urlparse
from .socket_config import socket_io
import random
from string import ascii_uppercase
import urllib.parse

api_routes = Blueprint("api", __name__)


def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        code_exist = SearchQueue.query.filter_by(queue_id=code).first()
        if not code_exist:
            break

    return code


@api_routes.route('/search')
def get_search_url():
    search_key = request.args.get('key')
    queue_id = request.args.get('queue_id')

    decoded_search_key = urllib.parse.unquote_plus(search_key)

    if search_key:
        key_item = HotelSearchKeys.query.filter_by(
            search_text=decoded_search_key).first()
        if key_item:
            return jsonify({"url": key_item.base_url}), 200
        else:
            search_item = HotelSearchKeys(decoded_search_key, None, queue_id)
            db.session.add(search_item)
            db.session.commit()

    return jsonify({"url": None}), 404


@api_routes.route('/post-results', methods=['POST'])
def post_results():
    update_type = request.json.get('update_type')

    try:
        result_message = "Success"
        if update_type == "send_hotel_link":
            data = request.json.get('data')
            search_text = data['search_text']

            search_item = HotelSearchKeys.query.filter_by(
                search_text=search_text).first()
            if search_item:
                search_item.base_url = data['base_url']

                db.session.commit()
                result_message = f"Updated base_url for {search_text}"

        if update_type == "send_hotel_list":
            data = request.json.get('data')
            search_text = data['search_text']

            searchKeyItem = HotelSearchKeys.query.filter_by(
                search_text=search_text).first()
            for result in data['results']:
                if result:
                    hotel = HotelInfo.query.filter_by(
                        hotel_name=result['name'], search_key=searchKeyItem.id).first()
                    if hotel is None:
                        hotel = HotelInfo(search_id=searchKeyItem.id,
                                          hotel_name=result['name'],
                                          address=result['address'],
                                          phone=result['phone'],
                                          url=result['url'])
                        db.session.add(hotel)
                        searchKeyItem.children.append(hotel)
                    else:
                        hotel.address = result['address']
                        hotel.phone = result['phone']
            db.session.commit()
            result_message = f"Hotels for {search_text} now added in database"

        return jsonify({"message": result_message}), 200
    except Exception as err:
        print(err)
        return jsonify({"message": err.args[0]}), 500


@api_routes.route("/get-locations")
def get_locations():
    locations = HotelSearchKeys.query.order_by(
        HotelSearchKeys.search_text).all()
    location_json = []

    for location in locations:
        location_json.append({
            "id": location.id,
            "search_key": location.search_text,
            "count": location.children.count(),
            "queue_code": location.queue_id
        })

    return jsonify({"locations": location_json}), 200


def getHotels(key, page=1):
    hotel_list = HotelSearchKeys.query.filter_by(
        search_text=key).first()
    if hotel_list:
        hotels = []
        resPaginator = None
        if page == "all":
            resultPage = hotel_list.children
        else:
            resPaginator = db.paginate(
                hotel_list.children, page=page, per_page=30)
            resultPage = resPaginator.items

        for hotel in resultPage:
            hotels.append({
                "id": hotel.id,
                "hotel_name": hotel.hotel_name,
                "address": hotel.address,
                "phone": hotel.phone,
                "url": hotel.url
            })
        return {"hotels": hotels, "max_page": resPaginator.pages if resPaginator else 0}
    else:
        return None


@api_routes.route('/get-hotels', methods=["GET"])
def get_hotels():
    search_key = request.args.get('key')
    page_level = request.args.get('page') or 1
    if search_key:
        hotel_list = getHotels(search_key, int(page_level))
        if hotel_list:
            return jsonify(hotel_list), 200

    return jsonify({"message": "No hotels found"}), 404


def start_scraping(search_text, code):
    current_host = f"{request.headers.get('Host')}"

    command = f"python ./backend/scraper/__init__.py {search_text} {current_host} {code}"
    subprocess.Popen(command, shell=True)


@api_routes.route('/start-scraping', methods=["POST"])
def scrape_precheck():
    search_text = request.json.get('search-text')

    check_status = SearchQueue.query.filter_by(search_text=search_text).order_by(
        SearchQueue.created_date.desc()).first()
    if check_status is None or (check_status.status != "ONGOING"):
        code = generate_unique_code(6)
        encoded_search_text = urllib.parse.quote_plus(search_text)
        start_scraping(encoded_search_text, code)

        # save tasks to database
        search_item = SearchQueue(queue_id=code,
                                  search_text=search_text)
        db.session.add(search_item)

        # inject search key if exists
        search_key = HotelSearchKeys.query.filter_by(
            search_text=search_text).first()
        if search_key:
            search_key.queue_id = code

        db.session.commit()

        return jsonify({"message": "Scraping now started", "queue_id": code}), 200
    else:
        return jsonify({"message": "An existing scraping task is still ongoing. Please try again later"}), 500


@api_routes.route('/download-file', methods=['GET'])
def download_file():
    search_text = request.args.get('key')
    if search_text:
        hotel_list = getHotels(search_text, "all")
        if hotel_list:
            data_dl = hotel_list["hotels"]

            df = pd.DataFrame.from_dict(data_dl)
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, sheet_name=search_text, index=False)

            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"{search_text}.xlsx", mimetype="application/vnd.ms-excel")

    return jsonify({"message": "An error occured during download"}), 500


def delete_location(search_text):
    check_location = HotelSearchKeys.query.filter_by(
        search_text=search_text).first()
    if check_location:
        db.session.delete(check_location)
        db.session.commit()
        return True
    else:
        return False


@api_routes.route('/delete-location', methods=['POST'])
def delete_location_api():
    search_text = request.json.get('search_text')
    start_delete = delete_location(search_text)
    if start_delete:
        return jsonify({"message": "Search key now deleted"}), 200
    else:
        return jsonify({"message": "An error occured while deleting this search item"}), 500


def report_to_socket(queue_id, message, status):
    task = SearchQueue.query.filter_by(queue_id=queue_id).first()
    if task:
        search_text = task.search_text

        task.status = status
        task.details = message

        count = 0
        location = HotelSearchKeys.query.filter_by(
            search_text=search_text).first()

        if location:
            count = location.children.count()
            location.queue_id = None  # clear queue_id on complete

        if status == "ERROR" and location.base_url is None:
            delete_location(search_text)

        db.session.commit()
        socket_io.send((count, queue_id, status))
        return True
    else:
        return False


@api_routes.route('/report', methods=["POST"])
def report_result():
    queue_id = request.json.get('queue_id')
    message = request.json.get('message')
    status = request.json.get('status')

    report_to_socket(queue_id, message, status)
    if report_to_socket:
        return jsonify({"message": "Scraping finished"}), 200
    else:
        return jsonify({"message": "Error when receiving report from worker"}), 500


@api_routes.route('/progress', methods=["POST"])
def progress_task():
    queue_id = request.json.get('queue_id')
    progress = request.json.get('progress')

    socket_io.emit("progress", (queue_id, progress))
    status = f"Task {queue_id} progressed to {progress} out of 5 steps"

    print(status)
    return jsonify({"message": status}), 200
