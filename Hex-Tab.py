from binascii import hexlify, unhexlify
from burp import IBurpExtender, IMessageEditorTabFactory, IMessageEditorTab


class BurpExtender(IBurpExtender, IMessageEditorTabFactory):

    # Implement IBurpExtender
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("Hex Tab")
        callbacks.registerMessageEditorTabFactory(self)

    # Implement IMessageEditorTabFactory
    def createNewInstance(self, controller, editable):
        return HexInputTab(self, controller, editable)


class HexInputTab(IMessageEditorTab):

    def __init__(self, extender, controller, editable):
        self._extender = extender
        self._helpers = extender._helpers
        self._editable = editable
        self._txtInput = extender._callbacks.createTextEditor()
        self._txtInput.setEditable(editable)

    # Implement IMessageEditorTab
    def getTabCaption(self):
        return "Hex Tab"

    def getUiComponent(self):
        return self._txtInput.getComponent()

    def isEnabled(self, content, isRequest):
        bodyOffset = self._helpers.analyzeRequest(content).getBodyOffset()
        return bodyOffset != len(content)

    def setMessage(self, content, isRequest):
        self._txtInput.setEditable(self._editable)
        # Remember the displayed content
        self._currentMessage = content
        # Split content into headers and body
        bodyOffset = self._helpers.analyzeRequest(content).getBodyOffset()
        self._currentHeaders = content[:bodyOffset]
        bodyText = content[bodyOffset:]

        bodyHex = hexlify(bodyText)
        # Insert spaces
        bodyHexSpaced = " ".join(
            bodyHex[i:i+2] for i in xrange(0, len(bodyHex), 2))
        # Insert New lines
        bodyHexLines = "\n".join(
            bodyHexSpaced[i:i+48] for i in xrange(0, len(bodyHexSpaced), 48))
        self._txtInput.setText(bodyHexLines)

    def getMessage(self):
        if not self.isModified():
            return self._currentMessage
        bodyHexFormatted = self._txtInput.getText()
        bodyHex = self._helpers.bytesToString(
            bodyHexFormatted).replace(" ", "").replace("\n", "")
        try:
            # Convert back to ascii and catch exception
            userInput = unhexlify(bodyHex)
        except TypeError:
            return self._currentMessage
        # Update the request body with the new body
        return self._currentHeaders + self._helpers.stringToBytes(userInput)

    def isModified(self):
        return self._txtInput.isTextModified()

    def getSelectedData(self):
        return self._txtInput.getSelectedText()
