from flask import Flask, request, jsonify
from itertools import product

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the optimization API"})

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.get_json()
    products_input = data['products']
    sheet_sizes = data['sheet_sizes']

    products = {p['name']: {'area': p['area'], 'qty': p['quantity']} for p in products_input}
    product_names = list(products.keys())
    max_counts = {p: int(max(sheet_sizes) // products[p]["area"]) + 1 for p in products}
    ranges = [range(0, max_counts[p] + 1) for p in products]

    best_layouts = []

    for sheet_area in sheet_sizes:
        best_result = None
        for combo in product(*ranges):
            layout = dict(zip(product_names, combo))
            total_area = sum(layout[p] * products[p]["area"] for p in layout)
            if total_area > sheet_area or total_area == 0:
                continue

            sheets_needed_list = [
                -(-products[p]["qty"] // layout[p]) if layout[p] > 0 else float("inf")
                for p in layout
            ]
            max_sheets = max(sheets_needed_list)
            total_printed = {p: layout[p] * max_sheets for p in layout}
            overprint = sum(max(0, total_printed[p] - products[p]["qty"]) for p in layout)

            if best_result is None or (max_sheets < best_result["sheets_needed"] or
                                       (max_sheets == best_result["sheets_needed"] and overprint < best_result["overprint"])):
                best_result = {
                    "sheet_size": sheet_area,
                    "layout": layout,
                    "total_area_per_sheet": total_area,
                    "sheets_needed": max_sheets,
                    "overprint": overprint
                }

        if best_result:
            best_layouts.append(best_result)

    # Select the best among all sheet sizes
    best = sorted(best_layouts, key=lambda x: (x["sheets_needed"], x["overprint"]))[0]

    return jsonify(best)
