import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import {FormControl, FormGroup, Validators} from '@angular/forms';
import {HttpClient} from '@angular/common/http';
import {Router} from '@angular/router';
import {StateService} from '../../services/state.service'

@Component({
  selector: 'app-importeventlog',
  templateUrl: './importeventlog.component.html',
  styleUrls: ['./importeventlog.component.css']
})
export class ImporteventlogComponent{

  @ViewChild('loglabelImport',{static: false})
  loglabelImport: ElementRef;

  @ViewChild('modellabelImport',{static: false})
  modellabelImport: ElementRef;

  formImport: FormGroup;
  logfileToUpload: File = null;
  modelfileToUpload: File = null;
  serverData: JSON;

  constructor(private stateService: StateService,private httpClient: HttpClient, private router: Router) {
    this.formImport = new FormGroup({
      importFile: new FormControl('', Validators.required)
    });

  }

  onLogFileChange(files: FileList) {
    this.loglabelImport.nativeElement.innerText = Array.from(files)
      .map(f => f.name)
      .join(', ');
    this.logfileToUpload = files.item(0);
  }

  onModelFileChange(files: FileList) {
    this.modellabelImport.nativeElement.innerText = Array.from(files)
      .map(f => f.name)
      .join(', ');
    this.modelfileToUpload = files.item(0);
  }

  import(): void {
    const uploadData = new FormData();
    uploadData.append('eventLog', this.logfileToUpload, this.logfileToUpload.name)
    uploadData.append('model', this.modelfileToUpload, this.modelfileToUpload.name)
    this.httpClient.post('http://127.0.0.1:5002/measurement', uploadData).subscribe(
      (data: any) =>{
        this.stateService.data = data;
        this.router.navigate(['/main/kpis']);
      }
    )
  }
}
