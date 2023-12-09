from . import app, db
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


@api_routes.route('/post-link', methods=['POST'])
def post_link():
    search_text = request.json.get('search_text')
    hotel_link = request.json.get('hotel_link')

    exists = db.session.query(HotelSearchKeys.id).filter_by(
        base_url=hotel_link).first() is not None
    message = "Naa naman ni sha"
    if not exists:
        search_item = HotelSearchKeys(search_text, hotel_link)
        db.session.add(search_item)
        db.session.commit()
        message = "Record now added"

    return jsonify({"message": message}), 200


@api_routes.route('/post-hotels', methods=['POST'])
def post_hotels():
    print("Saving here in api")
    message = "Success"
    results = request.json.get('data')
    search_text = request.json.get('search_text')

    searchKeyItem = HotelSearchKeys.query.filter_by(
        search_text=search_text).first()
    print(searchKeyItem.search_text)
    for result in results:
        if result:
            hotel = HotelInfo.query.filter_by(
                hotel_name=result, search_id=searchKeyItem.id)
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

    return jsonify({"message": message}), 200
