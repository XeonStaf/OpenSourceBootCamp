import { Routes } from '@angular/router';
import {AskPageComponent} from "./ask-page/ask-page.component";


export const routes: Routes = [
  {
    path: '',
    component: AskPageComponent
  },
  {
    path: 'ask',
    component: AskPageComponent
  },
  {
    path: '**',
    redirectTo: ''
  }
];
