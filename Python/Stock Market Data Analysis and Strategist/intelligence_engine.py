import ollama

class IntelligenceEngine:
    """
    The Brain: Uses Gemma 3 1B to convert raw data into A2UI actionable alerts.
    Now optimized to expect the single-stock focus (TCS).
    """
    def __init__(self, model_name='gpt-oss:20b-cloud'):
        self.model = model_name

    def generate_risk_report(self, market_data, govt_data, headlines):
        """
        Fuses multimodal data into a brief, non-technical description for the user.
        """
        # Safely extract the target stock data (TCS.NS)
        target_stock = "TCS.NS"
        stock_status = market_data.get(target_stock, {}).get('z_score', 0)
        
        # Extract just the titles for the AI prompt
        headline_texts = [h['title'] for h in headlines]

        # Build the prompt context
        prompt = f"""
        Role: Indian Financial Risk Expert.
        Data Context:
        - Inflation (CPI): {govt_data.get('cpi_inflation', 'N/A')}%
        - IIP Tech Growth: {govt_data.get('iip_tech_growth', 'N/A')}%
        - WPI Fuel Index: {govt_data.get('wpi_fuel_index', 'N/A')}
        - Headlines: {", ".join(headline_texts)}
        - TCS Volatility Z-Score: {stock_status}

        Task: Analyze the 'Tech-Sector Contraction' risk focused on TCS.
        Output Format (STRICTLY 2 LINES):
        Line 1: "What is happening": (Max 15 words)
        Line 2: "Action to take": (Max 10 words)
        """

        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ])
            content = response['message']['content']
            
            # Parse response
            lines = [line for line in content.strip().split('\n') if line.strip()]
            
            brief_text = lines[0].replace("Line 1:", "").replace("What is happening:", "").replace("1.", "").strip() if len(lines) > 0 else "Analysis unavailable."
            action_text = lines[1].replace("Line 2:", "").replace("Action to take:", "").replace("2.", "").strip() if len(lines) > 1 else "Hold positions."

            # Determine risk level based on the single problem criteria
            is_high_risk = govt_data.get('cpi_inflation', 0) > 6.0 or stock_status < -2.0
            
            return {
                "brief": brief_text,
                "action": action_text,
                "risk_level": "High" if is_high_risk else "Moderate"
            }
        except Exception as e:
            print(f"Ollama Engine Error: {e}")
            return {
                "brief": "AI Engine unavailable. Monitoring raw data signals.",
                "action": "Check manual alerts.",
                "risk_level": "Unknown"
            }