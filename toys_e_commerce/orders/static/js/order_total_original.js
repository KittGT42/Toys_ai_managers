(function($) {
    $(document).ready(function() {
        function updateTotalPrice() {
            var total = 0;
            $('.field-quantity input').each(function() {
                var quantity = parseInt($(this).val()) || 0;
                var row = $(this).closest('tr');
                var priceData = row.data('product-price');
                if (priceData) {
                    total += quantity * parseFloat(priceData);
                }
            });
            $('#id_total_price').val(total.toFixed(2));
        }

        // Оновлення при зміні кількості
        $(document).on('change', '.field-quantity input', updateTotalPrice);

        // Додавання data-атрибуту з ціною до рядків
        function initializePrices() {
            $('.field-quantity input').each(function() {
                var row = $(this).closest('tr');
                var productId = row.find('.field-product select').val();
                if (productId) {
                    $.get('/admin/api/product-price/' + productId, function(data) {
                        row.data('product-price', data.price);
                    });
                }
            });
        }

        initializePrices();
    });
})(django.jQuery);