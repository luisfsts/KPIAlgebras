# KPIAlgebras

#### Description:
>A framework that supports the prediction of future performance based on anticipated activity-level performance changes and control-flow changes. We have applied our approach to several real event logs, confirming our approach’s practical applicability

#### Dependencies: 
* Python environment:
  * pm4py
  * flask
  * flask_cors

* Node:
  * Download and install node.js
* Angular:
  * Run the commands:
    * npm install -g @angular/cli@latest
	* npm install --save-dev @angular-devkit/build-angular

* GraphViz:
  * Please check the instructions at https://pm4py.fit.fraunhofer.de/install-page#item-1-2 under the Install GraphViz section.

#### Running the tool:
* Run the app.py as a python file.
* Open a command prompt at the views directory and use the command 'ng serve'.
* Open the URL http://localhost:4200 in your browser.

#### Using the tool:
Begin using the tool by selecting an Event log(.xes or .csv) and a Process model(.ptml) and click on upload:
![Screenshot 2021-02-24 151357](https://user-images.githubusercontent.com/52032672/109017982-fcf5ec00-76b7-11eb-91bb-081c9ae7b80e.png)

The tool will then measure KPI values based on event data and, the process model will be displayed. 
![Screenshot 2021-02-24 155115](https://user-images.githubusercontent.com/52032672/109018181-2e6eb780-76b8-11eb-9ac2-a98f7c4fbc68.png)

Select any node of the Process tree to check KPI values related to it.
![Screenshot 2021-02-24 154625](https://user-images.githubusercontent.com/52032672/109017988-fd8e8280-76b7-11eb-8031-3c224f7234bf.png)

To change the KPI values of a leaf, select the desired node, the KPI, and the amount of change (e.g., 0.,1 = 10%) and click on compute. Such changes can be discarded by clicking on the "Undo change" or "Undo all changes" buttons. 	
![Screenshot 2021-02-24 151138](https://user-images.githubusercontent.com/52032672/109017979-fbc4bf00-76b7-11eb-8394-e31cfac07a41.png)

After a change, it is possible to compare the new values and original values.
![Screenshot 2021-02-24 154411](https://user-images.githubusercontent.com/52032672/109017986-fcf5ec00-76b7-11eb-9d4a-ad6925b75b9b.png)

To upload new pairs of Event log and Process tree, click on the import.
