from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token,jwt_required,get_jwt_identity

from rangers_shop.models import Customer, Product, ProdOrder, db,products_schema,product_schema, Order

api = Blueprint('api',__name__,url_prefix='/api')


@api.route('/token', methods= ['GET','POST'])
def token():
    data = request.json
    if data:
            client_id = data['client_id'] #looking for the key of client_id on the dictionary passed to us
            access_token = create_access_token(identity=client_id) 
            return {
                'status' : 200,
                'access_token' : access_token 
            }
        
    else:
            return {
                'status': 400,
                'message': 'Missing Client Id. Try Again'
            }

#creating our READ data request for shop

@api.route('/shop')
@jwt_required()
def get_shop():
    shop = Product.query.all() # its a list of objs, you cant send a list of objs thru api calls

    response = products_schema.dump(shop)
    return jsonify(response) # this will stringify the list to send to our front end 

#creating our READ data request for orders READ associated with 'GET' 

@api.route('/order/<cust_id>')
@jwt_required()
def get_order(cust_id):

    #We need to grab all the order_ids associated with the customer
    #Grab all the products on that particular order 

      
    prodorder = ProdOrder.query.filter(ProdOrder.cust_id == cust_id).all()

    data = []


    #need to traverse to grab all the products from each order 

    for order in prodorder: 
         #order is the prodorder object so has a prod_id associated with it

        product = Product.query.filter(Product.prod_id == order.prod_id).first()

        prod_data = product_schema.dump(product) #change this from an object to a dictionary 

        prod_data['quantity'] = order.quantity #coming from the prodorder table 
        prod_data['order_id'] = order.order_id  #want to associate this product with a specific order 
        prod_data['id'] = order.prodorder_id  #need to make products unique even if they are the same product 


        data.append(prod_data)

    return jsonify(data)


#create our CREATE data request for orders, usually associated with 'POST' 
@api.route('/order/create/<cust_id>', methods = ['POST'])
@jwt_required()
def create_order(cust_id):

    data = request.json

    customer_order = data['order'] 

    customer = Customer.query.filter(Customer.cust_id == cust_id).first()
    if not customer:
        customer = Customer(cust_id)
        db.session.add(customer)

    order = Order()
    db.session.add(order)

    #looping through the customer order list of dictionaries for each product

    for product in customer_order:

        prodorder = ProdOrder(product['prod_id'], product['quantity'], product['price'], order.order_id, customer.cust_id)
        db.session.add(prodorder)

        order.increment_order_total(prodorder.price)


        #decrement the available amount of that specific product in our shop
        current_product = Product.query.filter(Product.prod_id == product['prod_id']).first()

        
        current_product.decrement_quantity(product['quantity'])


        db.session.commit()

        return {
             'status' : 200,
             'message' :  'New Order was created!'
        }

# create our UPDATE route for our order


@api.route('/order/update/<order_id>', methods = ['PUT', 'POST']) 
@jwt_required()
def update_order(order_id):

    # try:

        data = request.json
        new_quantity = int(data['quantity'])
        prod_id = data['prod_id']

        prodorder = ProdOrder.query.filter(ProdOrder.order_id == order_id, ProdOrder.prod_id == prod_id).first()
        order = Order.query.get(order_id) #.get() is specific for ids 
        product = Product.query.get(prod_id)

    #update the product price based on the new quantity
        prodorder.set_price(product.price, new_quantity)

        diff = abs(prodorder.quantity - new_quantity)

    #based on if the new quantity is higher or lower we either new to decrement or increment total product quantity & order cost 
        if prodorder.quantity < new_quantity: 
            product.decrement_quantity(diff) #decrease our available inventory
            order.increment_order_total(prodorder.price) #our order total is going to be more 

        elif prodorder.quantity > new_quantity:
            product.increment_quantity(diff) #increase our available inventory
            order.decrement_order_total(prodorder.price) #our order total is going to be less 

        prodorder.update_quantity(new_quantity)

        db.session.commit()

        return {
            'status': 200,
            'message': 'Order was successfully updated!'
        }
    
    # except:

    #     return {
    #         'status': 400,
    #         'message': 'Unable to process your request. Please try again!'
    #     }

@api.route('/order/delete/<order_id>', methods = ['DELETE'])
@jwt_required()
def delete_item_order(order_id):

    data = request.json
    prod_id = data['prod_id']


    prodorder = ProdOrder.query.filter(ProdOrder.order_id == order_id, ProdOrder.prod_id == prod_id).first()

    order = Order.query.get(order_id)
    product = Product.query.get(prod_id)


    order.decrement_order_total(prodorder.price) #order total is gonna be less expensive 
    product.increment_quantity(prodorder.quantity) #add back to inventory 


    db.session.delete(prodorder)
    db.session.commit()

    return {
        'status': 200,
        'message' : 'Order was successfully deleted'
    }





        

       
