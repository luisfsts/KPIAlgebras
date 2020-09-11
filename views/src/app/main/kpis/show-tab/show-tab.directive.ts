import { Directive, ElementRef, Renderer2, HostListener } from '@angular/core';

@Directive({
    selector: '[showTab]'
})
export class ShowTabDirective{
    constructor(private elementRef: ElementRef, private renderer: Renderer2){
    }
    
    @HostListener('click')
    onClick() {
        this.renderer.setAttribute(this.elementRef.nativeElement,'class', 'nav-link active')
    }
}