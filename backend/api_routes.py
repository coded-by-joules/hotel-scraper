from . import db
from . database import *
from flask import Blueprint, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
import subprocess
import pandas as pd
from io import BytesIO

api_routes = Blueprint("api", __name__)


@api_routes.route('/search')
def get_search_url():
    search_key = request.args.get('key')
    if search_key:
        key_item = HotelSearchKeys.query.filter_by(
            search_text=search_key).first()
        if key_item:
            return jsonify({"url": key_item.base_url}), 200

    return jsonify({"url": None}), 404


@api_routes.route('/post-results', methods=['POST'])
def post_results():
    update_type = request.json.get('update_type')

    try:
        result_message = "Success"
        if update_type == "send_hotel_link":
            data = request.json.get('data')
            search_text = data['search_text']

            exists = db.session.query(HotelSearchKeys.id).filter_by(
                base_url=data['base_url']).first() is not None
            if not exists:
                search_item = HotelSearchKeys(
                    search_text, data['base_url'])
                db.session.add(search_item)
                db.session.commit()
                result_message = f"Successfully added {search_text} to database"
            else:
                result_message = f"{search_text} already in database"

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

        if update_type == "post_log":
            message = request.json.get('message')
            status = request.json.get('status')

            log_item = LogDetails(message, status)
            db.session.add(log_item)
            db.session.commit()

        return jsonify({"message": result_message}), 200
    except Exception as err:
        print(err)
        return jsonify({"message": err.args[0]}), 500


@api_routes.route("/get-locations")
def get_locations():
    locations = HotelSearchKeys.query.order_by(HotelSearchKeys.search_text).all()
    location_json = []

    for location in locations:
        location_json.append({
            "id": location.id,
            "search_key": location.search_text
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
            resPaginator = db.paginate(hotel_list.children, page=page, per_page=30)
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


def start_scraping(search_text):
    new_task = SearchQueue(search_text)

    command = f"python ./backend/scraper/__init__.py {search_text}"
    subprocess.Popen(command, shell=True)

    db.session.add(new_task)
    db.session.commit()


@api_routes.route('/start-scraping', methods=["POST"])
def scrape_precheck():
    search_text = request.json.get('search-text')

    check_status = SearchQueue.query.filter_by(search_text=search_text).order_by(
        SearchQueue.created_date.desc()).first()
    if check_status is None or check_status.status == "FINISHED":
        start_scraping(search_text)
        return jsonify({"message": f"Scraping for {search_text} started sucessfully"}), 200
    else:
        return jsonify({"message": "An existing scraping task is still ongoing. Please try again later"}), 500


@api_routes.route('/end-scraping', methods=["POST"])
def end_scraping():
    search_text = request.json.get('search_text')
    check_status = SearchQueue.query.filter_by(search_text=search_text).order_by(
        SearchQueue.created_date.desc()).first()

    if check_status:
        check_status.status = "FINISHED"
        db.session.commit()
        return jsonify({"message": f"Scraping for {search_text} is now finished"}), 200

    return jsonify({"message": "An error occured during scraping"}), 500


@api_routes.route('/download-file', methods=['GET'])
def download_file():
    search_text = request.args.get('key')
    if search_text:
        hotel_list = getHotels(search_text, "all")
        if hotel_list:
            data_dl = hotel_list

            df = pd.DataFrame.from_dict(data_dl)
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, sheet_name=search_text, index=False)

            output.seek(0)
            return send_file(output, as_attachment=True, download_name=f"{search_text}.xlsx", mimetype="application/vnd.ms-excel")

    return jsonify({"message": "An error occured during download"}), 500
