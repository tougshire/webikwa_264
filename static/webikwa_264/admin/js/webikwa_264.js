window.addEventListener("load", function(e) {
  document.getElementById("page-edit-form").addEventListener("click", function(e) {
    if(e.target.getAttribute('name')=="copy_image_url") {
        e.preventDefault()
        el_span = e.target.parentNode.parentNode.querySelector("[name='image_url']")
        el_copy = document.createElement("textarea")
        document.body.appendChild(el_copy)
        el_copy.innerHTML=el_span.innerHTML
        el_copy.select()
        document.execCommand("copy")
        document.body.removeChild(el_copy)
    }
  })
  
  document.getElementById("page-edit-form").addEventListener("change", function(e) {
    if(e.target.getAttribute('name')=="set_image_classfloat" || e.target.getAttribute('name')=="set_image_classwidth") {
        e.preventDefault()
        var el_span = e.target.parentNode.parentNode.querySelector("[name='image_url']")
        var imagewidth = e.target.parentNode.parentNode.querySelector("[name='set_image_classwidth']").value
        var imagefloat = e.target.parentNode.parentNode.querySelector("[name='set_image_classfloat']").value
        el_span.innerHTML = el_span.dataset.default.replace('class=""', 'class="' + imagewidth + ' ' + imagefloat + '"').replace('<','&lt;')
    }
    
  })

  // Add a button to collapse child forms within inline formsets
  // to make it easier to soert them
  //
  function setup_formset_collapser(formset_name) {

    var collapserbutton = document.createElement("button")
    var collapserbar = document.createElement('div');

    collapserbutton.classList.add("button", "button-small", "button-secondary")
    collapserbutton.innerText="expand/collapse " + formset_name.replaceAll("_"," ")

//    collapserbar.style.margin = '0 0 1rem';
    collapserbar.appendChild(collapserbutton)

    collapserbutton.addEventListener("click", function(e) {
      e.preventDefault()
      buttons=formset.querySelectorAll("button.w-panel__toggle")
      if( buttons.length ) {
        buttons[0].click()
      }
      for( button of buttons ) {
        if(button.ariaExpanded != buttons[0].ariaExpanded ) {
          button.click()
        }
      }
    })
    var formset = document.getElementById("id_" + formset_name + "-FORMS")
    formset.prepend(
      collapserbar
    )
  }

  /* setup_formset_collapser("articlepage_placements") */
  



    





})
