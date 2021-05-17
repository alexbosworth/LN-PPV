# Pay-per-View using the Lightning Network
Proof of Concept of a Pay-per-View content management solution using the [Lightning Network](https://lightning.network/).

## Current PPV implementations using the Lightning Network
Currently, most services (e.g. [yalls](https://yalls.org/)) serve only a portion of the data and use websockets to keep an open connection with the client. Only after the server confirms that the invoice has been paid, it sends the rest of the data.

While this solution works great in some cases, **what if you can't maintain a persistant websocket connection?**

## How it works
This PoC shows a way to statically serve PPV content by leveraging Lightning Network's invoice properties. Moreover it doesn't require any changes to the way payments are created and utilizes the following invoice fields:
* Amount
* Preimage hash
* Expiration time
* Description

Instead of sending the data partially, we can send the content in full but keep some parts encrypted with preimage of the HTLC as a key. A sample encrypted message could look like this:
```
--------- LN-PPV-START ---------
    <lnd invoice>
-------------------------------
    <encrypted content>
--------- LN-PPV-END ----------
```
Next, a piece of software on the side of the client (e.g. browser extension) would find the invoice block and after successful payment decrypt the content and display it to the user. There's no need for additional server-client communication (apart from payment settlement). 

Additionaly (depending on the usecase and security concerns) content encryption key can and oftenly should be different than the preimage and stored encrypted with the preimage as key in the payment description. This allows for the content encryption key to be much longer than 32-byte long preimage. This is crucially important if the content is served via an uprotected channel, where a routing node could also have the ability to decrypt the content.

## Possible usage examples

### Pay-per-Read Emails
Javascript is not supported inside emails. In it's current implementation, it's not possible to create a paywalled email, where the recipients need to pay for a privilege of reading the content. Using my proposed solution, paying the invoice (and encrypting the email) would look very similar to how PGP extensions built in email clients work (e.g. Thunderbird).

### Micropayments inside Tor hidden services
Since most of Tor hidden services don't use Javascript, there's no easy way to implement paywalled content without the need of constant refreshing by the user.
However, using this solution hidden services can serve PPV content without the need for any JS code. Please note that this would require for user to install an additional browser extension that reads the contents of the webpage and detects lightning invoices. While it might sound like a security risk (in the context of using Tor), it's much safer to install a possibly open-source and audited web browser extension rather than allowing for an arbitrary JS code execution. 
(also Tor browser comes with few extensions already pre-installed like HTTPS Everywhere and NoScript)

## Additionaly, all of examples above can have following properties:
### Time sensitive content
By changing the HTLC expiry field we can make the content time-sensitive while also handing the content (in an encrypted form) to another party. If the HTLC expires, the user can no longer recieve the payment Preimage rendering the encrypted content useless. Content provider doesn't even have to monitor whether the payment has been made.
What's also cool is the fact that the expiry time selection can be relatively long (max 1 year) or short (min 1 sec) depending on the usecase.

### Read privilege only for the quickest buyer
Let's say you want to share something publicly on Twitter but make it visible only to one person in a first come first serve fashion. Well, after the invoice has been paid, it becomes invalid for the rest. 
**Note: some nodes allow for the invoice to be paid multiple times so you need to check the configuration on your end.**

### Decryption sharing
By using the preimage as the decryption key, payer can (willingly or not - depending on the implementation and usecase) enable the routing nodes to also decrypt the content.

The usability of said property is especially visible in the "Pay-per-Read Email" usage example. Let's say Alice sends the same email to both Bob, Carol and Dolory. If the recipients know each other, Bob could possibly construct a payment where the routing nodes are Carol and Dolory. In that case Bob is essentially allowing borth Dolory and Carol to read the contents without paying anything.
```
                Alice                       |                   HTLC
                  ↓                         |               
        |To: Bob, Carol, Dolory |           |       Bob 🠖 Carol 🠖 Dolory 🠖 Alice
        | <ln-invoice>          |           |
        | <encrypted data>      |           |
```
This feature is of course not always wanted (I'd argue that it could be considered malicious in most of the cases). The simple and easy solution is for the content provider to use a separate encryption key for the data, encrypt it with the preimage and put it in the payment description field.
> Memo = Enc(DataKey, Preimage)

### Read confirmation without additional communication
This one is pretty straight-forward. By checking if the invoice corresponding to the user/request has been fulfilled (if the preimage has been revealed) content provider can determine wheter the other party has read the encrypted content and respond to next request from the same user accordingly.

## Proof-of-Concept
Attached in this repository is a simple Python script that allows you to create and decrypt the content. To test it out for yourself:
* Edit the `config.py` file supplying it with a path to admin macaroon and cert file

To create an encrypted packet place your content in a separate file and run:
```console
foo@bar:~$ python3 main.py -c <FILE_PATH>
```

Similarly, to decrypt the content place it in a separate file and run:
```console
foo@bar:~$ python3 main.py -d <FILE_PATH>
```
Make sure you've paid the invoice to successfully decrypt the content.

## License
MIT
