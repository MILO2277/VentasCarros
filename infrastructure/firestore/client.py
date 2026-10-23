import firebase_admin
from firebase_admin import credentials, firestore


def create_firestore_client(project_id=None):
	if not project_id:
		raise RuntimeError(
			"Configura FIRESTORE_PROJECT_ID o GOOGLE_CLOUD_PROJECT para usar Firestore."
		)
	try:
		app = firebase_admin.get_app()
	except ValueError:
		app = firebase_admin.initialize_app(
			credentials.ApplicationDefault(),
			{"projectId": project_id},
		)
	return firestore.client(app=app)