def get_analysis_prompt():
    return "You are an expert at image analysis related to urban design and architecture. You are given an image of an urban scene and you need to provide insights on the architectural style, color palette, futuristic elements, archetypes, and a short descriptive label for clustering. The insights should be converted into the given structure. "


def get_openai_input(base64_image, prompt):
    return [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "low",
                },
            ],
        }
    ]
