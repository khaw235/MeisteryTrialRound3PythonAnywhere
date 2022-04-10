from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Detail, Country, City, Sale
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from .serializers import LoginSerializer, UserSerializer, CountrySerializer,\
    SaleSerializer
from rest_framework.permissions import AllowAny
from django.contrib.auth import login
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from .forms import SalesDataForm
import numpy as np
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginAPI(generics.GenericAPIView):
    """
    This class creates the API for Login of a user.

    '''

    Attributes
    ----------
    permission_classes : rest-framework.permissions Object
        a variable to store the value of permissions
    serializer_class : LoginSerializer Class's Object
        a variable to attach a specific Serialezer with this API.
    
    Methods
    -------
    post(request, *args, **kwargs)
        stores the user's data after serializing and validating it.
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        """
        Step 1:
            Gets the serialzed data of the user, entered in frontend 
            of API.
        Step 2:
            Stores that data in 'serialzer' variable and validate it.
        Step 3:
            Saves the validated 'data' Object (a dictionary) in the 
            variable 'user'.

        Parameters
        ----------
        request : DRF HTTP POST Request Object
            data entered by the user on the frontend of the DRF
            REST API.

        Returns
        ------
        Dictionary
            a dictionary holding the values of the keys 'token' and 
            'user_id'.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        token, created = Token.objects.get_or_create(user=user)
        login(request, user)
        return Response({
            "token": str(token),
            "user_id": user.id
        })


class LogoutAPI(APIView): 
    """
    This class creates the API for Logout of a user.

    '''

    Methods
    -------
    get(request)
        logs out the user.
    """

    def get(self, request):
        """
        Logs out the user

        Parameters
        ----------
        request : DRF HTTP POST Request Object
            data entered by the user on the frontend of the DRF
            REST API.

        Returns
        ------
        Dictionary
            a dictionary the message.
        """

        request.user.auth_token.delete()

        return Response('User Logged out successfully')


class UserAPI(generics.GenericAPIView):
    """
    This class creates the API for User.

    '''

    Attributes
    ----------
    permission_classes : list
        a list to define who should have access to this API
    serializer_class : UserSerializer Class's Object
        a variable to attach a specific Serialezer with this API
    
    Methods
    -------
    get_object(request, id)
        returns value stored in 'user' key of 'request', a DRF HTTP
        POST Object (a dictionary).
    """

    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def get(self, request, id):
        detail = Detail.objects.get(user=User.objects.get(pk=id))
        usr = User.objects.get(pk=id)
        
        data = {
            'id': usr.id,
            'username': usr.username,
            'first_name': usr.first_name,
            'last_name': usr.last_name,
            'email': usr.email,
            'gender': detail.gender,
            'age': detail.age,
            'country': detail.country,
            'city': detail.city

        }

        return Response(data)

    def patch(self, request, id):
        usr = User.objects.get(pk=id)     
        detail = Detail.objects.get(user=usr)
        serializer = self.get_serializer(detail, data=request.data, partial=True)
        print(request.POST)
        
        if serializer.is_valid():
            serializer.save()
            print("SUCCESS")
            return Response(code=200)

        return JsonResponse(data="wrong parameters", safe=False)


class CountriesAPI(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = CountrySerializer

    def get(self, request):
        countries = Country.objects.all()
        full_data = []
        data = {
            'id': 0,
            'name': 'n',
            'cities': []
        }

        for country in countries:
            data['id'] = country.id
            data['name'] = country.name

            cities = City.objects.all()

            for city in cities:
                if city.country.id == data['id']:
                    data['cities'].append({
                        'id': city.id,
                        'name': city.name
                        })
            
        return Response(data)

    def post():
        pass


class SaleStatisticsAPI(APIView):
    def get(self, request):
        token = request.user.auth_token.key
        email = str(request.user.auth_token.user)
        current_user = User.objects.get(email=email)
        all_users_sales = Sale.objects.all()
        current_user_sales = Sale.objects.filter(user=current_user)
        current_user_total_revenue = 0.0
        current_user_total_sales = 0.0
        all_users_total_revenue = 0.0
        all_users_total_sales = 0.0
        current_user_revenues = []

        for sale in current_user_sales:
            current_user_total_revenue += float(sale.revenue)
            current_user_total_sales += float(sale.sales_number)
            current_user_revenues.append(float(sale.revenue))

        for sale in all_users_sales:
            all_users_total_revenue += float(sale.revenue)
            all_users_total_sales += float(sale.sales_number)

        current_user_highest_revenue = np.max(current_user_revenues)
        
        for sale in current_user_sales:
            revenue = float(sale.revenue)

            if revenue == current_user_highest_revenue:
                current_user_highest_revenue_id = sale.id
                current_user_highest_revenue_prod = sale.product


        data = {
            "average_sales_for_current_user": current_user_total_revenue /\
                 current_user_total_sales,
            "average_sale_all_user": all_users_total_revenue /\
                 all_users_total_sales,
            "highest_revenue_sale_for_current_user": {
                "sale_id": current_user_highest_revenue_id,
                "revenue": current_user_highest_revenue
            },
            "product_highest_revenue_for_current_user": {
                "product_name": current_user_highest_revenue_prod,
                "price": current_user_highest_revenue
            }
        }
        return Response(data)


class SaleAPI(generics.GenericAPIView):
    serializer_class = SaleSerializer

    def get(self, request):
        rec = []
        data = {}
        email = str(request.user.auth_token.user)
        user = User.objects.get(email=email)
        sales = Sale.objects.filter(user=user)

        for sale in sales:
            rec.append(
                {
                    "id": int(sale.id),
                    "product": str(sale.product),
                    "revenue": str(sale.revenue),
                    "sales_number": int(sale.sales_number),
                    "date": str(sale.date),
                    "user_id": int(user.id),
                }
            )

        data = {
            "DATA": rec
        }
        
        return Response(data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale_data = serializer.validated_data

        email = str(request.user.auth_token.user)
        user = User.objects.get(email=email)
        try:
            sale_obj = Sale.objects.get_or_create(
                date=sale_data['date'],
                product=sale_data['product'],
                revenue=sale_data['revenue'],
                sales_number=sale_data['sales_number'],
                user=user
            )
            
            data = {
                "id": sale_obj.id,
                "product": sale_obj.product,
                "revenue": sale_obj.revenue,
                "sales_number": sale_obj.sales_number,
                "date": sale_obj.date,
                "user_id": user.id

            }
            
            return Response(data)
        
        except:
            data = {
                "error": "Could not create Sale Object"
            }
            
            return Response(data)

class UpdateSaleAPI(generics.GenericAPIView):
    serializer_class = SaleSerializer

    def get(self, request, id):
        try:
            sale_obj = Sale.objects.get(id=id)
            sale_obj.delete()

            data = {
                "message": "Successfully deleted Sale Object"
            }

            return Response(data)

        except:
            data = {
                "error": "Sale object does not exists at " + str(id) + " id"
            }

            return Response(data)

    def patch(self, request, id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale_data = serializer.validated_data
        email = str(request.user.auth_token.user)
        user = User.objects.get(email=email)
        sale_obj = Sale.objects.get_or_create(id=id)        

        try:
            if sale_data['date'] != None:
                sale_obj.product = sale_data['date']

            if sale_data['product'] != None:
                sale_obj.product = sale_data['product']

            if sale_data['revenue'] != None:
                sale_obj.revenue = sale_data['revenue']

            if sale_data['sales_number'] != None:
                sale_obj.sales_number = sale_data['sales_number']

            sale_obj.save()
            
            data = {
                "id": sale_obj.id,
                "product": sale_obj.product,
                "revenue": sale_obj.revenue,
                "sales_number": sale_obj.sales_number,
                "date": sale_obj.date,
                "user_id": user.id

            }
            
            return Response(data)
        
        except:
            data = {
                "error": "Could not update Sale Object"
            }
            
            return Response(data)
        

    def patch(self, request, id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale_data = serializer.validated_data
        email = str(request.user.auth_token.user)
        user = User.objects.get(email=email)
        sale_obj = Sale.objects.get_or_create(id=id)        

        try:            
            sale_obj.product = sale_data['date']            
            sale_obj.product = sale_data['product']            
            sale_obj.revenue = sale_data['revenue']            
            sale_obj.sales_number = sale_data['sales_number']

            sale_obj.save()
            
            data = {
                "id": sale_obj.id,
                "product": sale_obj.product,
                "revenue": sale_obj.revenue,
                "sales_number": sale_obj.sales_number,
                "date": sale_obj.date,
                "user_id": user.id

            }
            
            return Response(data)
        
        except:
            data = {
                "error": "Could not update Sale Object"
            }
            
            return Response(data)


class UploadSaleData(View):
    template_name = 'accounts/salesdata.html'

    def get(self, request):
        form = SalesDataForm()
        context = {
            "form": form
        }

        return render(request, self.template_name, context)

    def post(self, request):
        CSV_DATA = []
        DATA_USER_EMAIL = ''

        DATA_USER_EMAIL = str(request.POST['email'])
        file = request.FILES['csv'].read().decode('utf-8')
        data = file.split('\n')
        data = data[1 : -1]

        for rec in data:
            CSV_DATA.append(rec.split(','))
        
        try:
            user = User.objects.get(email=DATA_USER_EMAIL)

            for rec in CSV_DATA:
                Sale.objects.get_or_create(
                    date=rec[0],
                    product=rec[1],
                    sales_number=rec[2],
                    revenue=rec[3],
                    user=user
                    )
            
            context = {
                'msg': "CSV data"
            }

            return render(request, 'accounts/uploaded.html', context)

        except:
            context = {
                'msg': "User does not exists at " + DATA_USER_EMAIL + \
                    ". CSV data could not be"
            }

            return render(request, 'accounts/uploaded.html', context)
