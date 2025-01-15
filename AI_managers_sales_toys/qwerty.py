import json
with open('bontoi_product_data.json') as f:
    data = json.load(f)

    for i in data:
        if i['article'] == '797':
            print(i)