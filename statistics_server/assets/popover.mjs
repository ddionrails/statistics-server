import { waitForElement } from "./waitForElement.mjs";

waitForElement("#confidence-popover").then((popover) => {
    const popoverButton = document.getElementById("confidence-popover-button")
    popoverButton.setAttribute("popovertarget", "confidence-popover")
    popover.setAttribute("popover", "")
    popover.classList.remove("hidden")

})