import {waitForElement} from "./waitForElement.mjs";


let variableType = new URLSearchParams(window.location.search).get("type");
if (variableType == "categorical") {
  waitForElement("#bargraph-checkbox").then((element) => {
    element.classList.remove("removed");
  });
  waitForElement("#proportional-data-explanation").then((element) => {
    element.classList.remove("removed")
  })
}

if (variableType == "numerical") {
  waitForElement("#boxplot-checkbox").then((element) => {
    waitForElement("#boxplot-flag").then((flag) => {
      const observer = new MutationObserver((_) => {
        // boxplot-flag is managed in dash code
        if(flag.innerHTML === "show"){
          element.classList.remove("removed");
        }
      });
      observer.observe(document.querySelector("#boxplot-flag"), {
        characterData: true,
        subtree: true,
      });
    })
  });
}

waitForElement(
  "#control-panel-checkbox >* input[type=checkbox]",
).then((checkbox) => {
  checkbox.addEventListener("change", (event) => {
    let checkbox = event.target;
    if (checkbox.checked) {
      document.querySelector(".control-panel").classList.add("removed");
    } else {
      document.querySelector(".control-panel").classList.remove("removed");
    }
  });
});

waitForElement(
  "#boxplot-checkbox >* input[type=checkbox]",
).then((checkbox) => {
  checkbox.addEventListener("change", (event) => {
    let checkbox = event.target;
    if (checkbox.checked) {
      document.getElementById("measure-dropdown-container").classList.add("hidden");
    } else {
      document.getElementById("measure-dropdown-container").classList.remove("hidden");
    }
  });
});
