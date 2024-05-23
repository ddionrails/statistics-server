
window.addEventListener('DOMContentLoaded', function() {
	let checkbox = document.querySelector("#control-panel-checkbox >* input[type=checkbox]")

	checkbox.addEventListener("change", (event) => {
		let checkbox = event.target
		if (checkbox.checked) {
			document.querySelector(".control-panel").classList.add("hidden")
		} else {
			document.querySelector(".control-panel").classList.remove("hidden")
		}
	});

})

