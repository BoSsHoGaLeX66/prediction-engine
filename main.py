from fastapi import FastAPI, HTTPException, UploadFile, Form, Request
from prophet import Prophet
import pandas as pd
import numpy as np
from fastapi.responses import StreamingResponse, RedirectResponse
import os
from fastapi.templating import Jinja2Templates
from azure.storage.blob import BlobServiceClient
from decouple import config
from fastapi.staticfiles import StaticFiles
import uvicorn




KEY = config('BLOB_STORE_PRED_STRING')

blob_service_client = BlobServiceClient.from_connection_string(KEY)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
global end_date
global file_name
prediction_created = False
uploaded = False
downloaded = False
already_uploaded = False

def get_upload():
    blob_client = blob_service_client.get_blob_client(container='uploads', blob=file_name)
    with open(file='upload.csv', mode='wb') as blob_csv:
        data = blob_client.download_blob()
        blob_csv.write(data.readall())
    df = pd.read_csv('upload.csv')
    os.remove('upload.csv')
    return df


def get_return():
    blob_client = blob_service_client.get_blob_client(container='returnfiles',
                                                      blob=str.replace(file_name, '.csv', '_predictions.csv'))
    with open(file='temp.csv', mode='wb') as blob_csv:
        data = blob_client.download_blob()
        blob_csv.write(data.readall())


def is_predicted(ds):
    if pd.to_datetime(ds) > pd.to_datetime(end_date):
        return True
    else:
        return False


def iterfile():
    with open(file='temp.csv', mode='rb') as file_like:
        yield from file_like

@app.post('/create_model')
async def create_model(periods: int = Form(), column: str = Form()):
    df = get_upload()

    #checks to make sure that the right columns are in the data frame and if they are correct it is converted into a numpy array
    possible_datetime_column_names = ['date', 'ds', 'datetime', 'date_time', 'Date', 'Datetime', 'DateTime', 'Date_Time', 'DS', 'Date_time']
    columns = df.columns

    date = 0
    for i in range(len(columns)):
        if columns[i] in possible_datetime_column_names:
            date = date + 1

    if date != 1:
        raise HTTPException(status_code=400, detail='Can not find datetime column')


    for i in range(5):
        if columns[i] in possible_datetime_column_names:
            date_column = columns[i]
            break

    ds = np.array(df[date_column])

    try:
        y = np.array(df[column])
    except:
        raise HTTPException(status_code=400, detail='column to use for prediction doesn\'t exist')

    if len(ds) < 300:
        raise HTTPException(status_code=400, detail='Not enough data to use to predict')

    if periods > (len(ds) * .1):
        raise HTTPException(status_code=400, detail='Can\'t predict that far into the future')


    #converts the validated data into a new data frame
    data = {'ds': pd.to_datetime(ds), 'y': y}
    cleaned_df = pd.DataFrame(data=data)
    global end_date
    end_date = cleaned_df['ds'].iloc[0]

    #creates that prophet model and if fails assumes data is non int
    m = Prophet()
    m.fit(cleaned_df)

    #creates future data frame and makes predictions
    future = m.make_future_dataframe(periods=periods)
    forecast = m.predict(future)

    forecast['predicted'] = forecast['ds'].apply(is_predicted)
    forecast['predicted'] = forecast['ds'].apply(is_predicted)

    #returns the predictions in a new csv file
    forecast.to_csv('temp.csv', index=False)
    blob_client = blob_service_client.get_blob_client(container='returnfiles', blob=str.replace(file_name, '.csv', '_predictions.csv'))
    with open(file='temp.csv', mode='rb') as data:
        blob_client.upload_blob(data)

    global prediction_created
    prediction_created = True

    return RedirectResponse('/', status_code=303)


@app.get('/download')
async def download():
    df = pd.read_csv('temp.csv')
    df_return = df[df['predicted'] == True]
    df_return.to_csv('temp.csv', index=False)
    response = StreamingResponse(iterfile(), media_type='text/csv')


    global prediction_created
    prediction_created = False

    global downloaded
    downloaded = True

    global file_name
    file_name = None

    return response

@app.post('/upload')
async def upload(file: UploadFile):
    # reads in the csv file to a data frame
    blob_container = blob_service_client.get_container_client(container='uploads')
    global file_name
    file_name = file.filename
    blob_list = [blob.name for blob in blob_container.list_blobs()]

    if file_name not in blob_list:
        blob_client = blob_service_client.get_blob_client(container='uploads', blob=file.filename)
        byte_data = await file.read()
        blob_client.upload_blob(byte_data)
        global uploaded
        uploaded = True

    else:
        global already_uploaded
        already_uploaded = True

        global prediction_created
        prediction_created = True


    return RedirectResponse('/', status_code=303)
@app.get('/')
async def main(request: Request):
    blob_container_uploads = blob_service_client.get_container_client(container='uploads')
    blob_container_return_files = blob_service_client.get_container_client(container='returnfiles')

    uploads_files = [blob.name for blob in blob_container_uploads.list_blobs()]
    return_files = [blob.name for blob in blob_container_return_files.list_blobs()]

    files_df = pd.DataFrame({'uploads': uploads_files, 'return': return_files})

    try:
        get_return()
    except:
        pass

    global downloaded
    if downloaded:
        os.remove('temp.csv')
        downloaded = False

    if already_uploaded and file_name != None:
        get_return()

    column_names = [None]
    df = None
    try:
        display = request.query_params['display']
    except:
        display = None
    try:
        df = pd.read_csv('temp.csv')
        df = df[['ds', 'yhat', 'predicted']]
        column_names = df.columns[0:2]

    except:
        pass
    is_int = [np.float64, np.int64]
    columns_select = None
    try:
        df_2 = get_upload()
        columns_select = []
        for column in df_2.columns:
            if type(df_2[column][0]) in is_int:
                columns_select.append(column)

    except:
        pass

    return templates.TemplateResponse('index.html', {'request': request, 'column_names': column_names, 'df': df, 'columns_select': columns_select, 'download': prediction_created, 'display': display, 'already_uploaded': already_uploaded, 'files_df': files_df})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



