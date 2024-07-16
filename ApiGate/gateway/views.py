from functools import wraps
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
import jwt
import requests
import logging
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm
logger = logging.getLogger(__name__)
import os

# URL of the Users Microservice
USERS_MS_URL = 'http://usersms:8002/users/'

# URL of the Books Microservice
BOOKS_MS_URL = 'http://bookms:8000/books/'



class HomeView(APIView):
    print('IM RUNNING')
    def get(self,request):
        user_info=request.session.get('user_info')
        print('here boy:',user_info)
        if user_info:
           response = requests.get('http://bookms:8000/books/')
           server_ip = os.environ.get('SERVER_IP')
           books = response.json()
           return render(request, 'home.html', {'books': books,'user_info': user_info,'SERVER_IP': server_ip})     
        else:
             return JsonResponse({'error': 'No user info'}, status=402)

class MyBooksView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        print('IM RUNNING my books')
        print('User ID:', user_id)
        
        if user_id:
            try:
                response = requests.post('http://loansms:8003/mybooks/', data={'user_id': user_id})
                print(f"Response status code: {response.status_code}")
                print(f"Response content: {response.content}")
                
                if response.status_code == 200:
                    try:
                        books = response.json()
                        print("The books: ", books)
                        server_ip = os.environ.get('SERVER_IP')
                        return render(request, 'mybooks.html', {'books': books, 'user_id': user_id, 'SERVER_IP': server_ip})
                    except ValueError:
                        return JsonResponse({'error': 'Invalid JSON response'}, status=500)
                else:
                    return JsonResponse({'error': 'Failed to fetch books from the API'}, status=response.status_code)
            except requests.RequestException as e:
                print(f'Error fetching books: {e}')
                return JsonResponse({'error': 'Failed to fetch books from the API'}, status=500)
        else:
            return JsonResponse({'error': 'No user info'}, status=402)

        
class BorrowAndDateSendView(APIView):
    def borrow_book(self, request):
        user_id = request.data.get('user_id')
        book_id = request.data.get('book_id')
        book_title = request.data.get('book_title')  # Receive book title from request data

        # Send borrow request to loans service
        borrow_data = {'user_id': user_id, 'book_id': book_id, 'book_title': book_title}  # Include book_title in borrow data
        response = requests.post('http://loansms:8003/loans/borrow/', data=borrow_data)
        
        if response.status_code == 200:
            server_ip = os.environ.get('SERVER_IP')
            form_html = response.json().get('form')
            return render(request, 'borrow.html', {
                'form': form_html,
                'user_id': user_id,
                'book_id': book_id,
                'book_title': book_title,
                'SERVER_IP': server_ip,
            })
        else:
            return JsonResponse({'error': 'Failed to borrow the book.'}, status=response.status_code)

    def send_date(self, request):
        return_date = request.data.get('return_date')
        user_id = request.data.get('user_id')
        book_id = request.data.get('book_id')
        book_title = request.data.get('book_title')  # Receive book title from request data
        
        if not return_date:
            return JsonResponse({'error': 'Missing date'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Send request to create loan with return date and book title
        loan_data = {
            'user_id': user_id,
            'book_id': book_id,
            'return_date': return_date,
            'book_title': book_title  # Include book title in loan creation data
        }
        response = requests.post('http://loansms:8003/loans/create/', data=loan_data)
        
        if response.status_code == 201:
            return JsonResponse({'message': 'Book return date set successfully.'}, status=status.HTTP_201_CREATED)
        else:
            return JsonResponse({'error': 'Failed to set return date.'}, status=response.status_code)

    def post(self, request):
        if 'return_date' in request.data:
            return self.send_date(request)
        else:
            return self.borrow_book(request)
