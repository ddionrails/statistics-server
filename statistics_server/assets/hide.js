function waitForElement(selector) {
  return new Promise((resolve) => {
    const observer = new MutationObserver((mutations) => {
      if (document.querySelector(selector)) {
        observer.disconnect();
        resolve(document.querySelector(selector));
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  });
}

let variableType = new URLSearchParams(window.location.search).get("type");
if (variableType == "categorical") {
  waitForElement("#bargraph-checkbox").then((element) => {
    element.classList.remove("hidden");
  });
}

if (variableType == "numerical") {
  waitForElement("#boxplot-checkbox").then((element) => {
    element.classList.remove("hidden");
  });
}

let checkbox = waitForElement(
  "#control-panel-checkbox >* input[type=checkbox]",
).then((checkbox) => {
  checkbox.addEventListener("change", (event) => {
    let checkbox = event.target;
    if (checkbox.checked) {
      document.querySelector(".control-panel").classList.add("hidden");
    } else {
      document.querySelector(".control-panel").classList.remove("hidden");
    }
  });
});
