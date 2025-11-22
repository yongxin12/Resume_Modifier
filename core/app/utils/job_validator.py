from flask import Request, jsonify

class JobValidator:
    @staticmethod
    def validate_request(request: Request):
        """Validate complete job description request"""
        try:
            # Validate content type
            if request.content_type != 'application/json':
                return jsonify({"error": "Content-Type must be application/json"}), 400, None
            
            # Get and validate JSON data
            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing request body"}), 400, None
                
            # Validate required fields
            if 'updated_resume' not in data or 'job_description' not in data:
                return jsonify({"error": "Both updated_resume and job_description are required"}), 400, None
                
            # Validate job description content
            job_description = data['job_description']
            if not job_description:
                return jsonify({"error": "No job description provided"}), 400, None
                
            if len(job_description) < 10:  # Minimum length
                return jsonify({"error": "Job description too short"}), 400, None
                
            if len(job_description) > 5000:  # Maximum length
                return jsonify({"error": "Job description too long"}), 400, None
                
            return None, None, data
            
        except Exception as e:
            return jsonify({"error": f"Request validation failed: {str(e)}"}), 400, None 