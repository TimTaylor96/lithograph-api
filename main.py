from flask import Flask, request, jsonify
from itertools import product
from math import ceil, sqrt

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the optimization API"})

@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON received"}), 400
        if 'products' not in data or 'sheet_sizes' not in data:
            return jsonify({"error": "Missing 'products' or 'sheet_sizes'"}), 400

        products_input = data['products']
        sheet_sizes = data['sheet_sizes']

        if not products_input or not sheet_sizes:
            return jsonify({"error": "Empty product or sheet size list"}), 400

        products = {
            p['name']: {'area': p['area'], 'qty': p['quantity']}
            for p in products_input
        }

        product_names = list(products.keys())
        max_counts = {
            p: int(max(sheet_sizes) // products[p]["area"]) + 1
            for p in products
        }
        ranges = [range(0, max_counts[p] + 1) for p in products]

        best_layouts = []

        # Simulated sheet dimensions (used to estimate spacing)
        sheet_dimensions = {
            400: (20, 20),
            900: (30, 30),
            875: (25, 35),
            1200: (30, 40),
            1750: (35, 50),
            2700: (45, 60),
            3500: (50, 70),
            4125: (55, 75),
            4800: (60, 80),
            5525: (65, 85)
        }

        for sheet_area in sheet_sizes:
            best_result = None
            sheet_width, sheet_height = sheet_dimensions.get(sheet_area, (sqrt(sheet_area), sqrt(sheet_area)))

            for combo in product(*ranges):
                layout = dict(zip(product_names, combo))
                total_items = sum(layout[p] for p in layout)
                if total_items == 0:
                    continue

                total_area = sum(layout[p] * products[p]["area"] for p in layout)
                if total_area > sheet_area:
                    continue

                # Estimate rows and cols assuming square-ish layout
                cols = ceil(sqrt(total_items))
                rows = ceil(total_items / cols)

                # Guillotine spacing options
                horizontal_spacing = (rows - 1) * sheet_width
                vertical_spacing = (cols - 1) * sheet_height
                spacing_area = min(horizontal_spacing, vertical_spacing)

                adjusted_total_area = total_area + spacing_area
                if adjusted_total_area > sheet_area:
                    continue

                # Estimate sheets needed
                sheets_needed_list = [
                    -(-products[p]["qty"] // layout[p]) if layout[p] > 0 else float("inf")
                    for p in layout
                ]
                max_sheets = max(sheets_needed_list)
                total_printed = {
                    p: layout[p] * max_sheets for p in layout
                }
                overprint = sum(
                    max(0, total_printed[p] - products[p]["qty"]) for p in layout
                )

                if best_result is None or (
                    max_sheets < best_result["sheets_needed"] or
                    (max_sheets == best_result["sheets_needed"] and overprint < best_result["overprint"])
                ):
                    best_result = {
                        "sheet_size": sheet_area,
                        "layout": layout,
                        "total_area_per_sheet": adjusted_total_area,
                        "sheets_needed": max_sheets,
                        "overprint": overprint
                    }

            if best_result:
                best_layouts.append(best_result)

        if not best_layouts:
            return jsonify({"error": "No viable layout found"}), 400

        best = sorted(best_layouts, key=lambda x: (x["sheets_needed"], x["overprint"]))[0]
        return jsonify(best)

    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
