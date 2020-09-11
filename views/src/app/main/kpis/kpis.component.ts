import { Component, OnInit } from '@angular/core';
import { StateService } from 'src/app/services/state.service';
import {HttpClient} from '@angular/common/http';
import { DomSanitizer } from '@angular/platform-browser';

@Component({
  selector: 'app-kpis',
  templateUrl: './kpis.component.html',
  styleUrls: ['./kpis.component.css']
})
export class KpisComponent implements OnInit {

  data:any;
  originalTreeData: any;
  historicData = [];
  selectedNode:any;
  selectedNodeOriginalData:any;
  selectedOperator:any;
  selectedKpi:any;
  operators = [];
  kpis=[];
  nodeName: string;
  delta: number;
  loopProbability: number;
  disableChangeOperator = true;
  disableChangeLeaf = true;
  hasChildren:boolean = false;
  svgData: any;
  historicSvgData = [];

  constructor(private stateService: StateService, private httpClient: HttpClient, private sanitizer: DomSanitizer) {

   }

  ngOnInit() {
    this.originalTreeData = this.stateService.data;
    this.data = this.stateService.data;
    this.operators = this.data.operators;
    this.kpis = ["service_time", "waiting_time"]
    this.svgData = this.sanitizer.bypassSecurityTrustUrl("data:image/svg+xml;base64," + this.data.svg)
    console.log(this.svgData)
  }

  selectNodeChangeHandler (event: any) {
    this.nodeName =  event.target.value;
    for (let node of this.data.nodes){
        if (node.name == this.nodeName){
            if (node.operator != null){
               this.hasChildren = true;
               if (this.selectedOperator != null){
                 this.disableChangeOperator = false
               }
            } else{
              this.hasChildren = false;
              this.selectedOperator = null;
              this.disableChangeOperator = true;
              this.disableChangeLeaf = false;
            }
          this.selectedNode = node
          var selectedNodeIndex = this.data.nodes.findIndex(node => node.name === this.selectedNode.name);
          this.selectedNodeOriginalData = this.data.originalState.nodes[selectedNodeIndex]
          console.log(this.selectedNode.kpis)
        }
    }
  }

  selectKpiChangeHandler (event: any) {
   this.selectedKpi =  event.target.value;
  }

  isChangeOperatorDisabled(){
    return this.disableChangeOperator
  }

  isUndoChangeDisabled(){
    if (this.historicData.length>0){
      return false
    } else {
      return true
    }
  }

   isChangeLeafDisabled(){
    return this.disableChangeLeaf
  }

  selectOperatorChangeHandler (event: any) {
    this.selectedOperator = event.target.value;
    if(this.selectedOperator != "Choose..."){
      this.disableChangeOperator = false;
    }
    console.log(this.selectedOperator);
  }

  redesign(){
    this.historicData.push(this.data)
    this.historicSvgData.push(this.svgData)
    var response = {}
    if (this.selectedOperator == "X"){
      var routingProbabilities = {}
      for (let children of this.selectedNode.children){
             if((<HTMLInputElement>document.getElementById(children)).value !== null &&
               (<HTMLInputElement>document.getElementById(children)).value !== ""){
               routingProbabilities[children] = (<HTMLInputElement>document.getElementById(children)).value;
             } else{
               routingProbabilities[children] = null;
             }
      }
      response = {"target_node": this.selectedNode,
                  "selectedOperator": this.selectedOperator,
                  "parameters":{"routing_probabilities":routingProbabilities}}
    } else if (this.selectedOperator == "*"){
      response = {"target_node": this.selectedNode,
                  "selectedOperator": this.selectedOperator,
                  "parameters":{"loop_probability":this.loopProbability}}
    } else{
      response = {"target_node": this.selectedNode.name,
                  "delta":this.delta,
                  "kpi": this.selectedKpi}
    }

    this.httpClient.post('http://127.0.0.1:5002/timeshifting', response).subscribe(
      (data: any) =>{
        this.data = data;
        this.svgData = this.sanitizer.bypassSecurityTrustUrl("data:image/svg+xml;base64," + this.data.svg)
        this.selectedNode = null;
        this.selectedNodeOriginalData = null;
        this.selectedOperator = null;
        if(this.delta != null){
          this.delta = null;
        }
      }
    )
  }

  undoChange(){
    this.httpClient.get('http://127.0.0.1:5002/undoChange').subscribe(
      (data: any) =>{
        this.data = data;
        this.svgData = this.sanitizer.bypassSecurityTrustUrl("data:image/svg+xml;base64," + this.data.svg)
        this.selectedNode = null;
        this.selectedNodeOriginalData = null;
        this.selectedOperator = null;
        this.historicData.pop()
        this.historicSvgData.pop()
      }
    )
  }

  undoAllChanges(){
    this.httpClient.get('http://127.0.0.1:5002/undoAllChanges').subscribe(
      (data: any) =>{
        this.data = data;
        this.svgData = this.sanitizer.bypassSecurityTrustUrl("data:image/svg+xml;base64," + this.data.svg)
        this.selectedNode = null;
        this.selectedNodeOriginalData = null;
        this.selectedOperator = null;
        this.historicData = []
        this.historicSvgData = []
      }
    )
  }
}
