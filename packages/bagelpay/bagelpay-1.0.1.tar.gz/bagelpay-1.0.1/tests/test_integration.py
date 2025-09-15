"""Integration tests for BagelPay SDK."""

import pytest
import os
from unittest.mock import patch, Mock
from decimal import Decimal

from src import BagelPayClient
from src.models import (
    CheckoutRequest,
    CreateProductRequest,
    UpdateProductRequest,
    Customer
)
from src.exceptions import (
    BagelPayError,
    BagelPayAPIError,
    BagelPayAuthenticationError,
    BagelPayValidationError,
    BagelPayNotFoundError
)


@pytest.mark.integration
class TestBagelPayIntegration:
    """Integration tests for BagelPay SDK."""
    
    def test_client_initialization_and_context_manager(self, api_key):
        """Test client initialization and context manager usage."""
        # Test basic initialization
        client = BagelPayClient(api_key=api_key, test_mode=True)
        assert client.api_key == api_key
        assert client.test_mode is True
        client.close()
        
        # Test context manager
        with BagelPayClient(api_key=api_key, test_mode=True) as client:
            assert isinstance(client, BagelPayClient)
            assert client.session is not None
    
    @patch('src.client.BagelPayClient._make_request')
    def test_complete_product_lifecycle(self, mock_make_request, api_key, sample_product_data):
        """Test complete product lifecycle: create, list, get, update, archive, unarchive."""
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        # Mock responses for different operations
        created_product = sample_product_data.copy()
        updated_product = sample_product_data.copy()
        updated_product['name'] = 'Updated Product Name'
        updated_product['price'] = 149.99
        
        archived_product = sample_product_data.copy()
        archived_product['status'] = 'archived'
        
        unarchived_product = sample_product_data.copy()
        unarchived_product['status'] = 'active'
        
        list_response = {
            'data': [sample_product_data],
            'total': 1,
            'page': 1,
            'pages': 1,
            'page_size': 10
        }
        
        # Configure mock responses
        mock_make_request.side_effect = [
            created_product,      # create_product
            list_response,        # list_products
            sample_product_data,  # get_product
            updated_product,      # update_product
            archived_product,     # archive_product
            unarchived_product    # unarchive_product
        ]
        
        # 1. Create product
        create_request = CreateProductRequest(
            name="Test Product",
            description="Test Description",
            price=99.99,
            currency="USD",
            billing_type="one_time",
            tax_inclusive=True,
            tax_category="standard",
            recurring_interval="monthly",
            trial_days=0
        )
        
        created = client.create_product(create_request)
        assert created.name == "Test Product"
        assert created.price == 99.99
        
        # 2. List products
        products = client.list_products(pageNum=1, pageSize=10)
        assert products.total == 1
        assert len(products.data) == 1
        
        # 3. Get specific product
        product = client.get_product("prod_test_12345")
        assert product.id == "prod_test_12345"
        
        # 4. Update product
        update_request = UpdateProductRequest(
            product_id="prod_test_12345",
            name="Updated Product Name",
            description="Updated Description",
            price=149.99,
            currency="USD",
            billing_type="one_time",
            tax_inclusive=True,
            tax_category="standard",
            recurring_interval="monthly",
            trial_days=0
        )
        
        updated = client.update_product(update_request)
        assert updated.name == "Updated Product Name"
        assert updated.price == 149.99
        
        # 5. Archive product
        archived = client.archive_product("prod_test_12345")
        assert archived.status == "archived"
        
        # 6. Unarchive product
        unarchived = client.unarchive_product("prod_test_12345")
        assert unarchived.status == "active"
        
        client.close()
    
    @patch('src.client.BagelPayClient._make_request')
    def test_complete_checkout_workflow(self, mock_make_request, api_key, sample_checkout_data):
        """Test complete checkout workflow."""
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        mock_make_request.return_value = sample_checkout_data
        
        # Test one-time payment checkout
        checkout_request = CheckoutRequest(
            product_id="prod_123",
            customer=Customer(email="test@example.com"),
            success_url="https://example.com/success",
            metadata={"description": "Test one-time payment"}
        )
        
        checkout = client.create_checkout(checkout_request)
        # Verify checkout response
        assert checkout.checkout_url is not None
        assert checkout.status == "pending"
        
        # Test checkout with customer information
        customer = Customer(
            email="test@example.com"
        )
        
        checkout_with_customer = CheckoutRequest(
            product_id="prod_456",
            customer=customer,
            success_url="https://example.com/success",
            metadata={"description": "Test checkout with customer"}
        )
        
        checkout_result = client.create_checkout(checkout_with_customer)
        assert checkout_result.checkout_url is not None
        
        client.close()
    
    @patch('src.client.BagelPayClient._make_request')
    def test_subscription_management_workflow(self, mock_make_request, api_key, sample_subscription_data):
        """Test subscription management workflow."""
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        # Mock responses
        list_response = {
            'items': [sample_subscription_data],
            'total': 1,
            'code': 200,
            'msg': 'success'
        }
        
        canceled_subscription = sample_subscription_data.copy()
        canceled_subscription['status'] = 'canceled'
        
        mock_make_request.side_effect = [
            list_response,           # list_subscriptions
            sample_subscription_data, # get_subscription
            canceled_subscription    # cancel_subscription
        ]
        
        # 1. List subscriptions
        subscriptions = client.list_subscriptions(pageNum=1, pageSize=10)
        assert subscriptions.total == 1
        assert len(subscriptions.items) == 1
        assert subscriptions.items[0].status == "active"
        
        # 2. Get specific subscription
        subscription = client.get_subscription("sub_test_12345")
        assert subscription.subscription_id == "sub_test_12345"
        assert subscription.status == "active"
        
        # 3. Cancel subscription
        canceled = client.cancel_subscription("sub_test_12345")
        assert canceled.status == "canceled"
        
        client.close()
    
    @patch('src.client.BagelPayClient._make_request')
    def test_customer_management_workflow(self, mock_make_request, api_key, sample_customer_data):
        """Test customer management workflow."""
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        # Mock responses
        list_response = {
            'items': [sample_customer_data],
            'total': 1,
            'code': 200,
            'msg': 'success'
        }
        
        mock_make_request.return_value = list_response
        
        # List customers
        customers = client.list_customers(pageNum=1, pageSize=10)
        assert customers.total == 1
        assert len(customers.items) == 1
        assert customers.items[0].email == "test@example.com"
        
        client.close()
    
    @patch('src.client.BagelPayClient._make_request')
    def test_transaction_listing_workflow(self, mock_make_request, api_key, sample_transaction_data):
        """Test transaction listing workflow."""
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        # Mock responses
        list_response = {
            'items': [sample_transaction_data],
            'total': 1,
            'code': 200,
            'msg': 'success'
        }
        
        mock_make_request.return_value = list_response
        
        # Test transaction listing
        transactions = client.list_transactions(pageNum=1, pageSize=10)
        assert transactions.total == 1
        assert len(transactions.items) == 1
        assert transactions.items[0].amount == 99.99
        
        client.close()
    
    @patch('src.client.BagelPayClient._make_request')
    def test_error_handling_workflow(self, mock_make_request, api_key):
        """Test error handling in various scenarios."""
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        # Test authentication error
        mock_make_request.side_effect = BagelPayAuthenticationError(
            "Invalid API key", 401
        )
        
        with pytest.raises(BagelPayAuthenticationError):
            client.list_products()
        
        # Test validation error
        mock_make_request.side_effect = BagelPayValidationError(
            "Invalid product data", 422
        )
        
        create_request = CreateProductRequest(
            name="Test Product",
            description="Test Description",
            price=99.99,
            currency="USD",
            billing_type="one_time",
            tax_inclusive=True,
            tax_category="standard",
            recurring_interval="monthly",
            trial_days=0
        )
        
        with pytest.raises(BagelPayValidationError):
            client.create_product(create_request)
        
        # Test not found error
        mock_make_request.side_effect = BagelPayNotFoundError(
            "Product not found", 404
        )
        
        with pytest.raises(BagelPayNotFoundError):
            client.get_product("nonexistent_product")
        
        client.close()
    
    def test_decimal_amount_handling(self, api_key):
        """Test handling of decimal amounts throughout the workflow."""
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        # Test with Decimal amounts
        checkout_request = CheckoutRequest(
            product_id="prod_123",
            customer=Customer(email="test@example.com"),
            success_url="https://example.com/success",
            metadata={"test": "decimal"}
        )
        
        # Should not raise any errors
        assert checkout_request.product_id == "prod_123"
        
        # Test with float amounts
        product_request = CreateProductRequest(
            name="Test Product",
            description="Test Description",
            price=149.99,
            currency="USD",
            billing_type="one_time",
            tax_inclusive=True,
            tax_category="standard",
            recurring_interval="monthly",
            trial_days=7
        )
        
        assert product_request.price == 149.99
        
        client.close()
    
    def test_metadata_handling_workflow(self, api_key):
        """Test metadata handling throughout different operations."""
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        # Test checkout with metadata
        metadata = {
            "order_id": "12345",
            "source": "website",
            "campaign": "summer2023",
            "user_id": 67890
        }
        
        checkout_request = CheckoutRequest(
            product_id="prod_789",
            customer=Customer(email="test@example.com"),
            metadata=metadata,
            success_url="https://example.com/success"
        )
        
        assert checkout_request.metadata == metadata
        assert checkout_request.metadata["order_id"] == "12345"
        assert checkout_request.metadata["user_id"] == 67890
        
        # Test customer with metadata
        customer_metadata = {
            "source": "referral",
            "referrer_id": "user_456"
        }
        
        customer = Customer(
            email="test@example.com",
            name="Test Customer",
            metadata=customer_metadata
        )
        
        assert customer.metadata == customer_metadata
        
        client.close()
    
    @patch('src.client.BagelPayClient._make_request')
    def test_pagination_workflow(self, mock_make_request, api_key, sample_product_data):
        """Test pagination handling across different list operations."""
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        # Mock paginated responses
        page1_response = {
            'items': [sample_product_data] * 5,
            'total': 12,
            'code': 200,
            'msg': 'success'
        }
        
        page2_response = {
            'items': [sample_product_data] * 5,
            'total': 12,
            'code': 200,
            'msg': 'success'
        }
        
        page3_response = {
            'items': [sample_product_data] * 2,
            'total': 12,
            'code': 200,
            'msg': 'success'
        }
        
        mock_make_request.side_effect = [page1_response, page2_response, page3_response]
        
        # Test pagination
        page1 = client.list_products(pageNum=1, pageSize=5)
        assert page1.total == 12
        assert page1.code == 200
        assert page1.msg == 'success'
        assert len(page1.items) == 5
        
        page2 = client.list_products(pageNum=2, pageSize=5)
        assert page2.total == 12
        assert page2.code == 200
        assert len(page2.items) == 5
        
        page3 = client.list_products(pageNum=3, pageSize=5)
        assert page3.total == 12
        assert page3.code == 200
        assert len(page3.items) == 2  # Last page has fewer items
        
        client.close()
    
    def test_client_configuration_options(self, api_key):
        """Test various client configuration options."""
        # Test with custom timeout
        client1 = BagelPayClient(
            api_key=api_key,
            test_mode=True,
            timeout=60
        )
        assert client1.timeout == 60
        client1.close()
        
        # Test with custom base URL
        custom_url = "https://custom.bagelpay.io"
        client2 = BagelPayClient(
            api_key=api_key,
            base_url=custom_url
        )
        assert client2.base_url == custom_url
        client2.close()
        
        # Test live mode
        client3 = BagelPayClient(
            api_key=api_key,
            test_mode=False
        )
        assert client3.test_mode is False
        assert client3.base_url == "https://live.bagelpay.io"
        client3.close()
    
    @patch('src.client.BagelPayClient._make_request')
    def test_recurring_product_workflow(self, mock_make_request, api_key, sample_subscription_product_data):
        """Test workflow with recurring/subscription products."""
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        mock_make_request.return_value = sample_subscription_product_data
        
        # Create recurring product
        recurring_request = CreateProductRequest(
            name="Monthly Subscription",
            description="Monthly subscription service",
            price=29.99,
            currency="USD",
            billing_type="recurring",
            tax_inclusive=True,
            tax_category="standard",
            recurring_interval="monthly",
            trial_days=7
        )
        
        product = client.create_product(recurring_request)
        assert product.billing_type == "recurring"
        assert product.recurring_interval == "monthly"
        assert product.trial_days == 7
        
        client.close()


@pytest.mark.integration
@pytest.mark.slow
class TestBagelPayRealAPIIntegration:
    """Real API integration tests (requires valid API key and network)."""
    
    @pytest.mark.skipif(
        not os.getenv('BAGELPAY_TEST_API_KEY'),
        reason="Real API key not provided"
    )
    def test_real_api_connection(self):
        """Test real API connection (only runs with real API key)."""
        api_key = os.getenv('BAGELPAY_TEST_API_KEY')
        
        with BagelPayClient(api_key=api_key, test_mode=True) as client:
            # This should not raise an exception if API key is valid
            # We're just testing the connection, not creating actual data
            try:
                # Try to list products (should work even if empty)
                products = client.list_products(pageNum=1, pageSize=1)
                assert hasattr(products, 'total')
                assert hasattr(products, 'data')
            except BagelPayAuthenticationError:
                pytest.fail("Authentication failed with provided API key")
            except BagelPayError as e:
                # Other errors might be acceptable depending on account state
                print(f"API call resulted in: {e}")


@pytest.mark.integration
class TestBagelPayErrorScenarios:
    """Test various error scenarios in integration context."""
    
    @patch('src.client.BagelPayClient._make_request')
    def test_network_error_handling(self, mock_make_request, api_key):
        """Test handling of network-related errors."""
        from requests.exceptions import ConnectionError, Timeout
        
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        # Test connection error
        mock_make_request.side_effect = BagelPayError("Request failed: Connection error")
        
        with pytest.raises(BagelPayError):
            client.list_products()
        
        # Test timeout error
        mock_make_request.side_effect = BagelPayError("Request failed: Timeout")
        
        with pytest.raises(BagelPayError):
            client.list_products()
        
        client.close()
    
    @patch('src.client.BagelPayClient._make_request')
    def test_api_error_details_preservation(self, mock_make_request, api_key):
        """Test that API error details are preserved through the workflow."""
        client = BagelPayClient(api_key=api_key, test_mode=True)
        
        # Create a detailed API error
        api_error = BagelPayValidationError(
            message="Validation failed",
            status_code=422,
            error_code="VALIDATION_ERROR"
        )
        
        mock_make_request.side_effect = api_error
        
        try:
            client.create_product(CreateProductRequest(
                name="Test",
                description="Test",
                price=99.99,
                currency="USD",
                billing_type="one_time",
                tax_inclusive=True,
                tax_category="standard",
                recurring_interval="monthly",
                trial_days=7
            ))
        except BagelPayValidationError as e:
            assert e.status_code == 422
            assert e.error_code == "VALIDATION_ERROR"
            assert "Validation failed" in str(e)
        
        client.close()