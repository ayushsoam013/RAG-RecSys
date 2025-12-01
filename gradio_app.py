import gradio as gr
import requests
import json

API_URL = "http://localhost:8000"

def format_product_html(product):
    """
    Formats a single product into an HTML card.
    """
    # Extract payload if it exists (Qdrant structure), otherwise use product as is
    payload = product.get("payload", product)
    
    img_url = payload.get("pc_item_img_original")
    if not img_url:
        img_url = "https://via.placeholder.com/150?text=No+Image"
    
    name = payload.get("pc_item_display_name", "Unknown Product")
    item_id = payload.get("pc_item_id", "N/A")
    price = payload.get("pc_item_fob_price")
    price_display = f"Price: {price}" if price else "Price: N/A"
    
    # Handle specs_json
    specs_html = ""
    specs_json = payload.get("specs_json")
    if specs_json:
        try:
            # It might be a string or already a dict
            if isinstance(specs_json, str):
                specs_data = json.loads(specs_json)
            else:
                specs_data = specs_json
            
            if isinstance(specs_data, dict) and specs_data:
                specs_html = "<div style='margin-top: 8px; font-size: 12px; color: black; border-top: 1px solid #eee; padding-top: 5px;'>"
                for k, v in specs_data.items():
                    specs_html += f"<div style='margin-bottom: 2px; color: black;'><span style='color: black'>{k}:</span> <span style='color: black'>{v}</span></div>"
                specs_html += "</div>"
        except Exception:
            pass # Ignore parsing errors

    html = f"""
    <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; border-radius: 5px; background-color: #f9f9f9; color: black;">
        <img src="{img_url}" style="width: 100%; max-height: 200px; object-fit: contain; margin-bottom: 10px;" alt="{name}">
        <h4 style="margin: 0 0 5px 0; font-size: 16px; color: black;">{name}</h4>
        <p style="margin: 0; font-size: 12px; color: black;">ID: {item_id}</p>
        <p style="margin: 0; font-size: 14px; font-weight: bold; color: black;">{price_display}</p>
        {specs_html}
    </div>
    """
    return html

def fetch_recommendations(product_id):
    """
    Fetches recommendations from both endpoints and formats them as HTML.
    """
    if not product_id:
        return "Please enter a Product ID", "Please enter a Product ID", "Please enter a Product ID", "Please enter a Product ID"
    
    try:
        # 0. Get Product Details
        product_detail_html = ""
        detail_response = requests.get(f"{API_URL}/product/{product_id}")
        if detail_response.status_code == 200:
            product_data = detail_response.json()
            # Wrap in a dict to match format_product_html expectation if needed, 
            # but format_product_html handles raw payload too if we adjust it or just pass it as is.
            # The endpoint returns the payload directly.
            product_detail_html = format_product_html(product_data)
        else:
            product_detail_html = f"<p style='color:red'>Error fetching details: {detail_response.status_code}</p>"

        # 1. Get Simple Retrieval Recommendations
        simple_payload = {"total_recommendations": 10}
        simple_response = requests.get(f"{API_URL}/recommendations/{product_id}", json=simple_payload)
        if simple_response.status_code == 200:
            simple_data = simple_response.json()
            simple_recs = simple_data.get("recommendations", [])
            simple_html = "".join([format_product_html(p) for p in simple_recs])
            if not simple_html:
                simple_html = "<p>No recommendations found.</p>"
        else:
            simple_html = f"<p style='color:red'>Error: {simple_response.status_code} - {simple_response.text}</p>"

        # 2. Get Re-ranked Recommendations
        # The generator endpoint expects a JSON body with product_id
        gen_payload = {"product_id": int(product_id), "total_recommendations": 10}
        gen_response = requests.post(f"{API_URL}/recommendations/generate", json=gen_payload)
        
        reasoning_html = ""
        reranked_html = ""

        if gen_response.status_code == 200:
            gen_data = gen_response.json()
            reranked_recs = gen_data.get("reranked_recommendations", [])
            reasoning = gen_data.get("reasoning", "")
            
            reasoning_html = f"<div style='margin-bottom: 10px; padding: 10px; background-color: #eef; border-radius: 5px; color: black;'><strong>Reasoning:</strong> {reasoning}</div>"
            reranked_html = "".join([format_product_html(p) for p in reranked_recs])
            
            if not reranked_recs:
                reranked_html = "<p>No re-ranked recommendations found.</p>"
        else:
            reasoning_html = f"<p style='color:red'>Error: {gen_response.status_code}</p>"
            reranked_html = f"<p style='color:red'>Error: {gen_response.text}</p>"
            
        return product_detail_html, simple_html, reasoning_html, reranked_html

    except Exception as e:
        return f"<p style='color:red'>Exception: {str(e)}</p>", f"<p style='color:red'>Exception: {str(e)}</p>", "", f"<p style='color:red'>Exception: {str(e)}</p>"

# Define Gradio Interface
with gr.Blocks(title="Recommendation System Comparison") as demo:
    gr.Markdown("# Recommendation System Comparison")
    
    with gr.Row():
        with gr.Column(scale=1):
            product_input = gr.Textbox(label="Enter Product ID", placeholder="e.g., 12782286")
            submit_btn = gr.Button("Get Recommendations", variant="primary")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Product Details")
            product_detail_output = gr.HTML(label="Product Details")

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Simple Retrieval (Vector Search)")
            simple_output = gr.HTML(label="Simple Retrieval Results")
        
        with gr.Column():
            gr.Markdown("### Re-ranked Recommendations (Generator)")
            reasoning_output = gr.HTML(label="Reasoning")
            reranked_output = gr.HTML(label="Re-ranked Results")

    submit_btn.click(
        fn=fetch_recommendations,
        inputs=[product_input],
        outputs=[product_detail_output, simple_output, reasoning_output, reranked_output]
    )

if __name__ == "__main__":
    demo.launch(server_port=7860)
