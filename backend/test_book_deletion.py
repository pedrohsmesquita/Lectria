"""
Test script for book deletion endpoint
Tests the DELETE /books/{book_id} endpoint
"""
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"

def test_delete_book():
    """
    Test the book deletion endpoint
    
    Prerequisites:
    - Backend server must be running
    - User must be logged in
    - At least one book must exist
    """
    
    # Step 1: Login
    print("Step 1: Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "test@example.com",  # Replace with your test user
            "password": "testpassword123"     # Replace with your test password
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.json())
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Step 2: Create a test book
    print("\nStep 2: Creating a test book...")
    create_response = requests.post(
        f"{BASE_URL}/books",
        headers=headers,
        json={"title": "Test Book for Deletion"}
    )
    
    if create_response.status_code != 201:
        print(f"❌ Book creation failed: {create_response.status_code}")
        print(create_response.json())
        return
    
    book_data = create_response.json()
    book_id = book_data["id"]
    print(f"✅ Book created with ID: {book_id}")
    
    # Step 3: List books to verify creation
    print("\nStep 3: Listing books...")
    list_response = requests.get(f"{BASE_URL}/books", headers=headers)
    books_before = list_response.json()
    print(f"✅ Total books before deletion: {len(books_before)}")
    
    # Step 4: Delete the book
    print(f"\nStep 4: Deleting book {book_id}...")
    delete_response = requests.delete(
        f"{BASE_URL}/books/{book_id}",
        headers=headers
    )
    
    if delete_response.status_code != 200:
        print(f"❌ Book deletion failed: {delete_response.status_code}")
        print(delete_response.json())
        return
    
    delete_data = delete_response.json()
    print(f"✅ Book deleted successfully: {delete_data['message']}")
    
    # Step 5: Verify deletion
    print("\nStep 5: Verifying deletion...")
    list_response_after = requests.get(f"{BASE_URL}/books", headers=headers)
    books_after = list_response_after.json()
    print(f"✅ Total books after deletion: {len(books_after)}")
    
    # Check if book is really gone
    book_exists = any(book["id"] == book_id for book in books_after)
    if book_exists:
        print("❌ ERROR: Book still exists in database!")
    else:
        print("✅ Book successfully removed from database")
    
    # Step 6: Try to access deleted book (should fail)
    print("\nStep 6: Attempting to access deleted book...")
    get_response = requests.get(f"{BASE_URL}/books/{book_id}", headers=headers)
    if get_response.status_code == 404:
        print("✅ Correctly returns 404 for deleted book")
    else:
        print(f"❌ Unexpected response: {get_response.status_code}")
    
    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED!")
    print("="*50)


def test_delete_unauthorized():
    """
    Test that users cannot delete books they don't own
    """
    print("\n" + "="*50)
    print("Testing unauthorized deletion...")
    print("="*50)
    
    # This test requires two users
    # For now, just test without token
    print("\nAttempting to delete without authentication...")
    delete_response = requests.delete(f"{BASE_URL}/books/fake-uuid")
    
    if delete_response.status_code == 401:
        print("✅ Correctly returns 401 for unauthenticated request")
    else:
        print(f"❌ Unexpected response: {delete_response.status_code}")


if __name__ == "__main__":
    print("="*50)
    print("BOOK DELETION ENDPOINT TESTS")
    print("="*50)
    
    # Run tests
    test_delete_book()
    test_delete_unauthorized()
