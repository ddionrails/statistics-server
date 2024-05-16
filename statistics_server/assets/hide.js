
window.addEventListener('load', function() {
	let checkbox = document.querySelector("#control-panel-checkbox >* input[type=checkbox]")
	let graph = this.document.querySelector(".graph-container")
	let originalWidth = graph.offsetWidth / window.innerWidth * 100

	checkbox.addEventListener("change", () => {
		if (checkbox.checked) {
			document.querySelector(".control-panel").classList.add("hidden")
			graph.style.width = "100vw"
		} else {
			document.querySelector(".control-panel").classList.remove("hidden")
			graph.style.width = originalWidth + "vw"
		}
	});

})

