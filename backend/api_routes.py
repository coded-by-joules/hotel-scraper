from . import db
from . database import *
from flask import Blueprint, jsonify, request

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
            exists = db.session.query(HotelSearchKeys.id).filter_by(
                base_url=data['base_url']).first() is not None
            if not exists:
                search_item = HotelSearchKeys(
                    data['search_text'], data['base_url'])
                db.session.add(search_item)
                db.session.commit()

        if update_type == "send_hotel_list":
            data = request.json.get('data')
            searchKeyItem = HotelSearchKeys.query.filter_by(
                search_text=data['search_text']).first()
            for result in data['results']:
                print(result)
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
    locations = HotelSearchKeys.query.all()
    location_json = []

    for location in locations:
        location_json.append({
            "id": location.id,
            "search_key": location.search_text,
            "base_url": location.base_url
        })
    return jsonify({"locations": location_json}), 200


@api_routes.route('/get-hotels', methods=["GET"])
def get_hotels():
    search_key = request.args.get('key')
    if search_key:
        hotel_list = HotelSearchKeys.query.filter_by(
            search_text=search_key).first()
        if hotel_list:
            hotels = []
            for hotel in hotel_list.children:
                hotels.append({
                    "id": hotel.id,
                    "hotel_name": hotel.hotel_name,
                    "address": hotel.address,
                    "phone": hotel.phone
                })
            return jsonify({"hotels": hotels}), 200

    return jsonify({"message": "No hotels found"}), 404
