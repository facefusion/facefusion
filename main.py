import os
import random
from run import start
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
import traceback
import uvicorn
import glob


app = FastAPI()


def delete_temp():
	for filename in glob.glob(".temp/*"):
		os.remove(filename)


@app.get("/ping")
def read_root():
	return {"ping": True}


@app.post("/face-swap")
def read_item(target: UploadFile, source: UploadFile):
	delete_temp()
	id_ = random.randint(1, 10000)

	target_name = f'.temp/target_{id_}.{target.filename.split(".")[-1]}'
	source_name = f'.temp/source_{id_}.{source.filename.split(".")[-1]}'
	output_name = f'.temp/output_{id_}.{target.filename.split(".")[-1]}'

	with open(target_name, 'wb') as f:
		f.write(target.file.read())

	with open(source_name, 'wb') as f:
		f.write(source.file.read())

	try:
		start(target_name, source_name, output_name)
	except:
		print(traceback.format_exc())
		return {"status": False}

	return FileResponse(path=output_name, filename=f'output_{id_}.{source.filename.split(".")[-1]}', media_type='multipart/form-data')


if __name__ == "__main__":
	uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
