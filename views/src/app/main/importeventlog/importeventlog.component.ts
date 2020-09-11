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

  @ViewChild('labelImport',{static: false})
  labelImport: ElementRef;

  formImport: FormGroup;
  fileToUpload: File = null;
  serverData: JSON;

  constructor(private stateService: StateService,private httpClient: HttpClient, private router: Router) {
    this.formImport = new FormGroup({
      importFile: new FormControl('', Validators.required)
    });

  }

  onFileChange(files: FileList) {
    this.labelImport.nativeElement.innerText = Array.from(files)
      .map(f => f.name)
      .join(', ');
    this.fileToUpload = files.item(0);
  }

  import(): void {
    const uploadData = new FormData();
    uploadData.append('eventLog', this.fileToUpload, this.fileToUpload.name)
    this.httpClient.post('http://127.0.0.1:5002/measurement', uploadData).subscribe(
      (data: any) =>{
        this.stateService.data = data;
        this.router.navigate(['/main/kpis']);
      }
    )
  }
}
