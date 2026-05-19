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
})
