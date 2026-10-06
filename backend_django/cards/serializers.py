from rest_framework import serializers
from .models import Card

class CardSerializer(serializers.ModelSerializer):
    card_number = serializers.CharField(write_only=True, min_length=16, max_length=16)

    class Meta:
        model = Card
        fields = [
            'id', 'cardholder_name', 'masked_card', 'last_4',
            'card_type', 'expiry_month', 'expiry_year', 'created_at',
            'card_number'
        ]
        read_only_fields = ['id', 'masked_card', 'last_4', 'card_type', 'created_at']

    def validate_card_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Card number must contain only numeric digits.")
        return value

    def create(self, validated_data):
        card_number = validated_data.pop('card_number')
        last_4 = card_number[-4:]
        first_4 = card_number[:4]
        masked = f"{first_4}-XXXX-XXXX-{last_4}"

        if card_number.startswith('4'):
            card_type = 'Visa'
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            card_type = 'Mastercard'
        elif card_number.startswith(('60', '65', '81', '82')):
            card_type = 'RuPay'
        else:
            card_type = 'Generic'

        user = self.context['request'].user
        card = Card.objects.create(
            user=user,
            masked_card=masked,
            last_4=last_4,
            card_type=card_type,
            **validated_data
        )
        return card