Created by: Alex Searle\
Start Date: 5/24/2023

Added Collaborator: Ranjay Kumar

This is a simple project using fastapi to take in a csv file, a number of periods to predict, and then the column of data that should be predicted. This csv file is then taken in and checked to see if the need data for modeling is present. This data is then taken and converted into numpy arrays, which is then used to create a pandas data frame with the proper headers. Then this cleaned data frame is used to create a model with facebook prophet. Then a future data frame is created and prophet is used to predict the values for this data time frame in a new data frame called forecast which only contains the future values. Forecast is then converted back into a csv file and returned to the user as an attachment with the FileResponse class of fast api.
## Instructions:
1. Make sure that you have git and docker installed
2. Clone the Github repo using _git clone https://github.com/BoSsHoGaLeX66/fbprophet_api.git_
2. After the cloning go to the folder and start up a cmd
3. Then run _docker build . -t prediction:1.0_
4. Then run _docker run -p 8000:8000 prediction:1.0_
5. Then navigate to localhost:8000 and use the application
