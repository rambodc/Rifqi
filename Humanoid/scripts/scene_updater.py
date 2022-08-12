# Imports the Google Cloud client library
import os
from google.cloud import storage

USD_BUCKET_NAME = "irobotx-usd-scenes"
LOCAL_USD_WORKING_DIR = "C:/Users/Rifqi Dewangga/Documents"

# me - this DAT
# scriptOp - the OP which is cooking
#
# press 'Setup Parameters' in the OP to call this function to re-create the parameters.
def onSetupParameters(scriptOp):
	"""Auto-generated by Component Editor"""
	# manual changes to anything other than parJSON will be	# destroyed by Comp Editor unless doc string above is	# changed

	TDJSON = op.TDModules.mod.TDJSON
	parJSON = """
	{
		"CloudStorage": {
			"Updatescene": {
				"name": "Updatescene",
				"label": "UpdateScene",
				"page": "CloudStorage",
				"style": "Pulse",
				"default": false,
				"enable": true,
				"startSection": false,
				"readOnly": false,
				"enableExpr": null,
				"help": ""
			}
		}
	}
	"""
	parData = TDJSON.textToJSON(parJSON)
	TDJSON.addParametersFromJSONOp(scriptOp, parData, destroyOthers=True)

# called whenever custom pulse parameter is pushed
def onPulse(par):
	if par.name == "Updatescene":
		print("Retrieving scene from cloud...")
		update_working_dir()
		download_all_assets(USD_BUCKET_NAME)
		print("Scene successfully updated")
		reinit_usd_op()

def onCook(scriptOp):
	scriptOp.clear()
	return

def create_directory_for_file(filename):
	path = os.path.dirname(filename)

	if os.path.exists(path): return

	os.makedirs(path)

def download_all_assets(bucket_name):
	storage_client = storage.Client()

	blobs = storage_client.list_blobs(bucket_name)

	for blob in blobs:
		filepath = f"{LOCAL_USD_WORKING_DIR}/{blob.name}"
		create_directory_for_file(filepath)
		blob.download_to_filename(filepath)

		print(f"Downloaded storage object {blob.name} from bucket {bucket_name} to local file {filepath}")

def update_scene_files():
	blobs = get_all_blobs(USD_BUCKET_NAME)

	for blob in blobs:
		local_filename = f"{LOCAL_USD_WORKING_DIR}/{blob.name}"
		download_all_assets(USD_BUCKET_NAME, blob.name, local_filename)

def reinit_usd_op():
	op('usd1').par.imp.pulse()

def update_working_dir():
	working_dir = op('config')[0,1]

	global LOCAL_USD_WORKING_DIR
	LOCAL_USD_WORKING_DIR = working_dir
	print(f"Set USD working directory to: {LOCAL_USD_WORKING_DIR}")

def main():
	# update_scene_files()
	print("main called")

if __name__ == "__main__":
	main()