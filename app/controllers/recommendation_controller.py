from config.qdrantConfig import qdrant_client_wrapper
from app.schemas import RecommendationResponse, GeneratorRequest, GeneratorResponse
import dspy
import json

# class ReRankSignature(dspy.Signature):
#     """
#     You are an expert E-Commerce Recommendation Re-Ranking Engine. Your task is to re-rank a list of "Candidate Products" to ensure they are most relevant to a specific "Anchor Product" that a buyer is currently viewing.

#     ## BUYER PSYCHOLOGY & RANKING LOGIC
#     To determine relevance, you must adopt the perspective of a potential buyer in the {{category}}.

#     ## INPUT VARIABLES
#     1. **Anchor Product:** {{anchor_product}} (The product the buyer is currently looking at).
#     2. **Category:** {{category}} (The specific market category).
#     3. **Candidate Products:** {{candidate_products}} (The list of items retrieved from the database).

#     ## INSTRUCTIONS

#     **Step 1: Dynamic Category Analysis (Buyer Perspective)**
#     Analyze the provided `{{category}}` variable. Adopt the persona of a knowledgeable buyer shopping in this specific domain.
#     * Identify the intrinsic attributes and "Key Buying Factors" that drive a purchase decision for this specific category.
#     * Determine which specifications or details (e.g., technical specs, materials, compatibility, dimensions, or brand tier) are non-negotiable for a buyer looking for a substitute or comparison.

#     **Step 2: Compare and Rank**
#     Compare each item in the `{{candidate_products}}` list against the `{{anchor_product}}` using the factors identified in Step 1. Re-order the list based on the following logic:
#     1.  **Direct Substitutes (Highest Priority):** Products that match the Anchor's core utility and identified Key Buying Factors (e.g., same model series, similar specs, or equivalent brand tier). These are items a buyer would seriously consider if the Anchor was out of stock.
#     2.  **Thematic Matches:** Products that differ slightly in specs or brand but serve the exact same user intent and usage context.
#     3.  **Loose Matches:** Products in the same category but with significantly different utility (e.g., luxury vs. budget, or professional vs. amateur grade).

#     **Step 3: The Fallback Protocol**
#     If the provided product details are sparse (missing ISQs/attributes) or the context is unclear:
#     * Disregard complex attribute analysis.
#     * Rank purely based on **Semantic Name Similarity**. Prioritize products where the Name/Title indicates the closest match in intent to the Anchor Product.

#     ## CONSTRAINTS
#     1.  **Count Consistency:** You must return the EXACT SAME number of items as provided in the `{{candidate_products}}` list. Never add or remove items.
#     2.  **No Hallucinations:** Do not infer attributes that are not explicitly present in the data.
#     3.  **Output Format:** The `ranked_product_ids` output must be a raw JSON list of the re-ranked Product IDs.

#     ### OUTPUT FORMAT EXAMPLE
#     [ "ID_123", "ID_456", "ID_789" ]
#     """
#     anchor_product = dspy.InputField(desc="The product currently being viewed (Name, Category, ISQs/Attributes)")
#     category = dspy.InputField(desc="The specific market category of the Anchor Product")
#     candidate_products = dspy.InputField(desc="A list of retrieved products (ID, Name, Attributes) from the vector database")
#     ranked_product_ids = dspy.OutputField(desc="JSON array of Product IDs in the new, re-ranked order")

class ReRankSignature(dspy.Signature):
    """
    You are an expert E-Commerce Recommendation Re-Ranking Engine.
    Your task is to re-rank a list of candidate products to ensure
    they are most relevant to a specific anchor product the buyer
    is currently viewing.

    ## Buyer Psychology & Ranking Logic
    Adopt the perspective of a knowledgeable buyer within the given category.
    Identify the core utility and key buying factors that typically influence
    purchasing decisions in this domain (e.g., specs, materials, brand tier,
    compatibility, technical performance, dimensions, etc.).

    ## Instructions

    **1. Dynamic Category Analysis**
    - Analyze the provided category.
    - Determine which attributes or specifications are essential for determining
      whether a candidate product is a direct substitute, thematic match,
      or loosely related alternative.

    **2. Compare and Rank**
    Compare each item in `candidate_products` against the `anchor_product`
    using the identified key buying factors.

    Rank candidates based on the following priority:
      1. **Direct Substitutes** — Strong overlap in core utility and key factors
         (e.g., same series, highly similar specs, equivalent brand tier).
      2. **Thematic Matches** — Serve the same usage intent with moderate differences.
      3. **Loose Matches** — Same general category but meaningfully different in purpose
         (budget vs. premium, amateur vs. professional, etc.).

    **3. Fallback Protocol**
    If product details are sparse or unclear:
    - Skip detailed attribute analysis.
    - Rank based purely on semantic similarity of product names and titles.

    ## Constraints
    - **Count Consistency:** Return the exact same number of items as in
      `candidate_products`. No additions or removals.
    - **No Hallucinations:** Do not infer attributes not provided in the data.
    - **Output Format:** `ranked_product_ids` must be a raw JSON list of
      the re-ranked product IDs.

    ## Example Output
    [ "ID_123", "ID_456", "ID_789" ]
    """

    anchor_product = dspy.InputField(
        desc="The product currently being viewed (Name, Category, Attributes/ISQs)"
    )
    category = dspy.InputField(
        desc="The specific category of the anchor product"
    )
    candidate_products = dspy.InputField(
        desc="A list of retrieved products (ID, Name, Attributes)"
    )
    ranked_product_ids = dspy.OutputField(
        desc="JSON array of Product IDs in the re-ranked order"
    )


async def get_product_embedding(product_id: int):
    """Retrieve product vector and metadata"""
    try:
        result = qdrant_client_wrapper.client.retrieve(
            collection_name="product_data",
            ids=[product_id],
            with_vectors=True,
            with_payload=True
        )
        
        if not result:
            raise ValueError(f"Product {product_id} not found")
        
        return result[0].vector, result[0].payload
    except Exception as e:
        raise ValueError(f"Error retrieving product {product_id}: {e}")

async def get_recommendations_logic(product_id: int, total_recommendations: int = 5) -> RecommendationResponse:
    # 1. Get the product embedding
    vector, payload = await get_product_embedding(product_id)
    
    # 2. Search for similar products
    search_result = qdrant_client_wrapper.client.query_points(
        collection_name="product_data",
        query=vector,
        limit=total_recommendations,
        with_payload=True
    ).points
    
    # Filter out the product itself if it appears in results (optional but good practice)
    recommendations = [
        {"id": hit.id, "score": hit.score, "payload": hit.payload}
        for hit in search_result
        if hit.id != product_id
    ]
    
    return RecommendationResponse(
        product_id=product_id,
        recommendations=recommendations
    )

async def generate_recommendations_logic(request: GeneratorRequest) -> GeneratorResponse:
    # 1. Get current product details (for context)
    _, current_product_payload = await get_product_embedding(request.product_id)
    
    # Extract category
    category_name = "Honda Portable Generator"
    
    # 2. Get base recommendations
    base_recs_response = await get_recommendations_logic(request.product_id, total_recommendations=request.total_recommendations or 5)
    candidates = base_recs_response.recommendations
    
    # 3. Re-rank using DSPy
    reranker = dspy.ChainOfThought(ReRankSignature)
    
    # Convert to strings for LLM
    current_product_str = json.dumps(current_product_payload, default=str)
    candidates_str = json.dumps(candidates, default=str)
    
    prediction = reranker(
        anchor_product=current_product_str,
        category=category_name,
        candidate_products=candidates_str
    )
    
    # 4. Parse the result
    try:
        # Attempt to clean the output if it contains markdown code blocks
        cleaned_output = prediction.ranked_product_ids.replace("```json", "").replace("```", "").strip()
        ranked_ids = json.loads(cleaned_output)
        
        # Reconstruct the list of objects based on the returned IDs
        # Create a mapping for quick lookup
        candidate_map = {item['id']: item for item in candidates}
        
        reranked_list = []
        for pid in ranked_ids:
            # Handle potential type mismatch (int vs str) or missing IDs
            pid_int = int(pid) if str(pid).isdigit() else pid
            if pid_int in candidate_map:
                reranked_list.append(candidate_map[pid_int])
        
        # Add any missing candidates that were dropped (Output Integrity guardrail fallback)
        existing_ids = set(item['id'] for item in reranked_list)
        for item in candidates:
            if item['id'] not in existing_ids:
                reranked_list.append(item)
                
    except (json.JSONDecodeError, AttributeError, ValueError):
        # Fallback: if parsing fails, return original list but with a note in reasoning
        reranked_list = candidates
        prediction.reasoning += " (Failed to parse re-ranked list, returning original)"

    # Ensure reasoning is available (ChainOfThought adds it to prediction)
    reasoning_text = getattr(prediction, 'reasoning', "No reasoning provided.")

    return GeneratorResponse(
        product_id=request.product_id,
        reranked_recommendations=reranked_list,
        reasoning=reasoning_text
    )

async def get_product_details_logic(product_id: int):
    """Retrieve just the product payload for details view"""
    try:
        result = qdrant_client_wrapper.client.retrieve(
            collection_name="product_data",
            ids=[product_id],
            with_vectors=False,
            with_payload=True
        )
        
        if not result:
            raise ValueError(f"Product {product_id} not found")
        
        return result[0].payload
    except Exception as e:
        raise ValueError(f"Error retrieving product {product_id}: {e}")
