from lettucedetect.models.inference import HallucinationDetector

# For a transformer-based approach:
detector = HallucinationDetector(
    method="transformer", model_path="KRLabsOrg/lettucedect-base-modernbert-en-v1"
)

contexts = "阿尔伯特·爱因斯坦出生于德国乌尔姆，是一位著名的物理学家。"
question = "爱因斯坦出生在哪?"
answer = "爱因斯坦出生于德国的柏林。"

# Get span-level predictions indicating which parts of the answer are considered hallucinated.
predictions = detector.predict(context=contexts, question=question, answer=answer, output_format="spans")
print("Predictions:", predictions)

# Predictions: [{'start': 31, 'end': 71, 'confidence': 0.9944414496421814, 'text': ' The population of France is 69 million.'}]
