"""Tests for BagelPay SDK PyPI Package Usage.

This test module specifically tests the functionality of the bagelpay-andrew-test-2024
package installed from TestPyPI.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException, Timeout

# Test if the PyPI package can be imported
try:
    from bagelpay.client import BagelPayClient
    from bagelpay.models import (
        Product,
        CheckoutRequest,
        CheckoutResponse,
        CreateProductRequest,
        UpdateProductRequest,
        Transaction,
        ProductListResponse,
        TransactionListResponse,
        Customer,
        Subscription,
        SubscriptionListResponse,
        CustomerListResponse
    )
    from bagelpay.exceptions import (
        BagelPayError,
        BagelPayAPIError,
        BagelPayAuthenticationError,
        BagelPayValidationError,
        BagelPayNotFoundError
    )
    PYPI_PACKAGE_AVAILABLE = True
except ImportError:
    PYPI_PACKAGE_AVAILABLE = False
    # Create mock classes for testing when package is not available
    class BagelPayClient:
        pass
    class Product:
        pass
    class CheckoutRequest:
        pass
    class CreateProductRequest:
        pass
    class BagelPayError(Exception):
        pass
    class BagelPayAPIError(BagelPayError):
        pass
    class BagelPayAuthenticationError(BagelPayError):
        pass


class TestPyPIPackageAvailability:
    """Test PyPI package availability and import."""
    
    def test_pypi_package_import(self):
        """Test that the PyPI package can be imported."""
        if not PYPI_PACKAGE_AVAILABLE:
            pytest.skip("PyPI package not installed. Install with: pip install -i https://test.pypi.org/simple/ bagelpay-andrew-test-2024==1.0.0")
        
        # If we reach here, the package was imported successfully
        assert PYPI_PACKAGE_AVAILABLE is True
    
    def test_client_class_available(self):
        """Test that BagelPayClient class is available from PyPI package."""
        if not PYPI_PACKAGE_AVAILABLE:
            pytest.skip("PyPI package not installed")
        
        assert BagelPayClient is not None
        assert hasattr(BagelPayClient, '__init__')
    
    def test_models_available(self):
        """Test that model classes are available from PyPI package."""
        if not PYPI_PACKAGE_AVAILABLE:
            pytest.skip("PyPI package not installed")
        
        # Test core models
        assert Product is not None
        assert CheckoutRequest is not None
        assert CreateProductRequest is not None
        assert UpdateProductRequest is not None
        assert Transaction is not None
    
    def test_exceptions_available(self):
        """Test that exception classes are available from PyPI package."""
        if not PYPI_PACKAGE_AVAILABLE:
            pytest.skip("PyPI package not installed")
        
        # Test exception hierarchy
        assert BagelPayError is not None
        assert BagelPayAPIError is not None
        assert BagelPayAuthenticationError is not None
        assert BagelPayValidationError is not None
        assert BagelPayNotFoundError is not None
        
        # Test inheritance
        assert issubclass(BagelPayAPIError, BagelPayError)
        assert issubclass(BagelPayAuthenticationError, BagelPayError)


@pytest.mark.skipif(not PYPI_PACKAGE_AVAILABLE, reason="PyPI package not installed")
class TestPyPIClientInitialization:
    """Test BagelPayClient initialization from PyPI package."""
    
    def test_client_initialization_test_mode(self):
        """Test client initialization in test mode using PyPI package."""
        client = BagelPayClient(
            api_key="test_key",
            test_mode=True
        )
        
        assert client.api_key == "test_key"
        assert client.test_mode is True
        assert client.base_url == "https://test.bagelpay.io"
        assert client.timeout == 30
        assert client.session.headers['x-api-key'] == "test_key"
        assert client.session.headers['Content-Type'] == "application/json"
        assert "BagelPay-Python-SDK" in client.session.headers['User-Agent']
    
    def test_client_initialization_live_mode(self):
        """Test client initialization in live mode using PyPI package."""
        client = BagelPayClient(
            api_key="live_key",
            test_mode=False
        )
        
        assert client.api_key == "live_key"
        assert client.test_mode is False
        assert client.base_url == "https://api.bagelpay.io"
        assert client.timeout == 30
    
    def test_client_initialization_custom_timeout(self):
        """Test client initialization with custom timeout using PyPI package."""
        client = BagelPayClient(
            api_key="test_key",
            timeout=60
        )
        
        assert client.timeout == 60
    
    def test_client_context_manager(self):
        """Test client as context manager using PyPI package."""
        with BagelPayClient(api_key="test_key") as client:
            assert client.api_key == "test_key"


@pytest.mark.skipif(not PYPI_PACKAGE_AVAILABLE, reason="PyPI package not installed")
class TestPyPIClientRequests:
    """Test BagelPayClient request methods from PyPI package."""
    
    @patch('bagelpay.client.requests.Session')
    def test_make_request_success(self, mock_session_class):
        """Test successful request using PyPI package."""
        # Setup mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "test_id", "name": "test"}
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Test
        client = BagelPayClient(api_key="test_key")
        result = client._make_request("GET", "/test")
        
        assert result == {"id": "test_id", "name": "test"}
        mock_session.request.assert_called_once_with(
            "GET", "https://test.bagelpay.io/test", timeout=30
        )
    
    @patch('bagelpay.client.requests.Session')
    def test_make_request_authentication_error(self, mock_session_class):
        """Test authentication error handling using PyPI package."""
        # Setup mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid API key",
                "code": "authentication_failed"
            }
        }
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Test
        client = BagelPayClient(api_key="invalid_key")
        
        with pytest.raises(BagelPayAuthenticationError) as exc_info:
            client._make_request("GET", "/test")
        
        assert "Invalid API key" in str(exc_info.value)
    
    @patch('bagelpay.client.requests.Session')
    def test_make_request_network_error(self, mock_session_class):
        """Test network error handling using PyPI package."""
        # Setup mock
        mock_session = Mock()
        mock_session.request.side_effect = RequestException("Network error")
        mock_session_class.return_value = mock_session
        
        # Test
        client = BagelPayClient(api_key="test_key")
        
        with pytest.raises(BagelPayError) as exc_info:
            client._make_request("GET", "/test")
        
        assert "Network error" in str(exc_info.value)


@pytest.mark.skipif(not PYPI_PACKAGE_AVAILABLE, reason="PyPI package not installed")
class TestPyPIProductMethods:
    """Test product methods from PyPI package."""
    
    @patch('bagelpay.client.BagelPayClient._make_request')
    def test_create_product(self, mock_make_request):
        """Test product creation using PyPI package."""
        # Setup mock response
        mock_product_data = {
            "id": "prod_test123",
            "name": "Test Product",
            "description": "A test product",
            "price": 29.99,
            "currency": "USD",
            "type": "one_time",
            "active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        mock_make_request.return_value = mock_product_data
        
        # Test
        client = BagelPayClient(api_key="test_key")
        request = CreateProductRequest(
            name="Test Product",
            description="A test product",
            price=29.99,
            currency="USD",
            type="one_time"
        )
        
        product = client.create_product(request)
        
        assert isinstance(product, Product)
        assert product.id == "prod_test123"
        assert product.name == "Test Product"
        assert product.price == 29.99
        
        mock_make_request.assert_called_once_with(
            "POST", "/products", data=request.to_dict()
        )
    
    @patch('bagelpay.client.BagelPayClient._make_request')
    def test_list_products(self, mock_make_request):
        """Test product listing using PyPI package."""
        # Setup mock response
        mock_response = {
            "products": [
                {
                    "id": "prod_test123",
                    "name": "Test Product",
                    "description": "A test product",
                    "price": 29.99,
                    "currency": "USD",
                    "type": "one_time",
                    "active": True,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            ],
            "total": 1,
            "page": 1,
            "per_page": 10
        }
        mock_make_request.return_value = mock_response
        
        # Test
        client = BagelPayClient(api_key="test_key")
        response = client.list_products()
        
        assert isinstance(response, ProductListResponse)
        assert len(response.products) == 1
        assert response.total == 1
        assert response.products[0].id == "prod_test123"
        
        mock_make_request.assert_called_once_with("GET", "/products", params={})


@pytest.mark.skipif(not PYPI_PACKAGE_AVAILABLE, reason="PyPI package not installed")
class TestPyPICheckoutMethods:
    """Test checkout methods from PyPI package."""
    
    @patch('bagelpay.client.BagelPayClient._make_request')
    def test_create_checkout_session(self, mock_make_request):
        """Test checkout session creation using PyPI package."""
        # Setup mock response
        mock_checkout_data = {
            "id": "checkout_test123",
            "url": "https://checkout.bagelpay.io/checkout_test123",
            "product_id": "prod_test123",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
            "customer_email": "test@example.com",
            "status": "pending",
            "created_at": "2024-01-01T00:00:00Z",
            "expires_at": "2024-01-01T01:00:00Z"
        }
        mock_make_request.return_value = mock_checkout_data
        
        # Test
        client = BagelPayClient(api_key="test_key")
        request = CheckoutRequest(
            product_id="prod_test123",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            customer_email="test@example.com"
        )
        
        checkout = client.create_checkout_session(request)
        
        assert isinstance(checkout, CheckoutResponse)
        assert checkout.id == "checkout_test123"
        assert checkout.url == "https://checkout.bagelpay.io/checkout_test123"
        assert checkout.product_id == "prod_test123"
        
        mock_make_request.assert_called_once_with(
            "POST", "/checkout", data=request.to_dict()
        )


@pytest.mark.skipif(not PYPI_PACKAGE_AVAILABLE, reason="PyPI package not installed")
class TestPyPIErrorHandling:
    """Test error handling from PyPI package."""
    
    def test_exception_inheritance(self):
        """Test that exceptions maintain proper inheritance using PyPI package."""
        # Test base exception
        base_error = BagelPayError("Base error")
        assert str(base_error) == "Base error"
        
        # Test API error
        api_error = BagelPayAPIError("API error", status_code=400)
        assert isinstance(api_error, BagelPayError)
        assert api_error.status_code == 400
        
        # Test authentication error
        auth_error = BagelPayAuthenticationError("Auth error")
        assert isinstance(auth_error, BagelPayError)
        
        # Test validation error
        validation_error = BagelPayValidationError("Validation error")
        assert isinstance(validation_error, BagelPayError)
        
        # Test not found error
        not_found_error = BagelPayNotFoundError("Not found error")
        assert isinstance(not_found_error, BagelPayError)
    
    @patch('bagelpay.client.BagelPayClient._make_request')
    def test_error_handling_in_methods(self, mock_make_request):
        """Test error handling in client methods using PyPI package."""
        # Setup mock to raise authentication error
        mock_make_request.side_effect = BagelPayAuthenticationError("Invalid API key")
        
        client = BagelPayClient(api_key="invalid_key")
        
        with pytest.raises(BagelPayAuthenticationError):
            client.list_products()
        
        with pytest.raises(BagelPayAuthenticationError):
            request = CreateProductRequest(
                name="Test",
                description="Test",
                price=10.0,
                currency="USD",
                type="one_time"
            )
            client.create_product(request)


@pytest.mark.skipif(not PYPI_PACKAGE_AVAILABLE, reason="PyPI package not installed")
class TestPyPIIntegration:
    """Integration tests for PyPI package."""
    
    def test_end_to_end_workflow_mock(self):
        """Test end-to-end workflow with mocked responses using PyPI package."""
        with patch('bagelpay.client.BagelPayClient._make_request') as mock_request:
            # Setup mock responses
            mock_product = {
                "id": "prod_test123",
                "name": "Test Product",
                "description": "A test product",
                "price": 29.99,
                "currency": "USD",
                "type": "one_time",
                "active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
            
            mock_checkout = {
                "id": "checkout_test123",
                "url": "https://checkout.bagelpay.io/checkout_test123",
                "product_id": "prod_test123",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel",
                "status": "pending",
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": "2024-01-01T01:00:00Z"
            }
            
            # Configure mock to return different responses for different calls
            mock_request.side_effect = [mock_product, mock_checkout]
            
            # Test workflow
            client = BagelPayClient(api_key="test_key")
            
            # Create product
            product_request = CreateProductRequest(
                name="Test Product",
                description="A test product",
                price=29.99,
                currency="USD",
                type="one_time"
            )
            product = client.create_product(product_request)
            
            # Create checkout session
            checkout_request = CheckoutRequest(
                product_id=product.id,
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel"
            )
            checkout = client.create_checkout_session(checkout_request)
            
            # Verify results
            assert product.id == "prod_test123"
            assert checkout.id == "checkout_test123"
            assert checkout.product_id == product.id
            
            # Verify mock calls
            assert mock_request.call_count == 2


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])