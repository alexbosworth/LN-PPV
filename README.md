# Pay-per-View using the Lightning Network
Proof of Concept of a static Pay-per-View content management solution using the [Lightning Network](https://lightning.network/).

## Current PPV implementations using the Lightning Network
Currently, most services (e.g. [yalls](https://yalls.org/)) serve only a portion of the data and use websockets to keep an open connection with the client. Only after the server confirms that the invoice has been paid, it sends the rest of the data.

While this solution works great in some cases, **what if you can't maintain a persistant websocket connection?**

## How it works
This PoC shows a way to statically serve PPV content by leveraging Lightning Network's invoice properties. Moreover it doesn't require any changes to the way payments are created and utilizes the following invoice fields:
* Amount
* Preimage hash
* Expiration time
* Description

Instead of sending the data partially, we can send the content in full but keep some parts encrypted with data key encrypted by the preimage.

> Description = AES(Key, Preimage)

A sample encrypted message could look like this:
```
----------------------- LN-PPV-START -----------------------
lntb100n1ps2y4gvpp5syqxv44j5hjsl8gsrwjrhkamnglf7degutpkmc4xc
7dwfvk555vqdxdtp4rv7n8x3mrsmp0d3m8vvt02fujk7rcfs4kwemy2pf5v3
64vft4snmfvcehwvekxf49zc2tx4grxuzxwpp556p4far5v630vexkzm2d24
dx2nmwfdp9zemwxdzy2k359arnv6zewce5vwzs2fgryvngdd6xztmtxap4xv
fnve88gurw29x4jd3523e8qsmgdapy2mmftye9gcqzpgxqrrsssp5f9xl74j
v44x05dqtr7dyltq8mkl7hhnfugtj43h2yts25v3wqazq9q8zqqyssql6228
y08yxdncy80kt838p0m6n2g57n0mqvvc67frlqh4yfyypnrsd6usaqeyn4pl
nl9rhrr86999nal563p84szcyhr57kn94gygssq4k30zv
------------------------------------------------------------
5a6b735279726c4b39496b6b676577614b4b67386c7563717042434d6e30
6a414a746d39674564654f3661384e312f616e6866465437724372644b6b
2b4b7a3577544c6b6d2b432b644b704f4b42757779377337553543636f50
3851746644366e7252492b6b7638724858765a6b594b5646533476595532
6f6c48754436747131494b572f7a534d6679546d694d6169775956754161
32565059745a4a75474d384e7877476d4f497a4d624b5377385555307238
536232642b7a6a6c5737456e6e4e34346b6a6e68672f6245795545546344
                          (...)
42613536527738523448305157552b6b766b63417157325543454d797975
495437546866332f30463271446c37337251496546757a52557534686868
75596b755256757367584836715656305a33637949795961302b365a3333
396e6b6a722f5777376c365470556937613030477370306e53654b31622b
2f58304d52756d7268704b634d433546653370783173384b446961472f66
39664151624f3642382b446c456c2b584374787832585262776971774748
753436347479554e6b597776334b646b526d6b3278794d665567376f6438
767257514e356c66706167447462304c4f38682b35424146434d62563357
----------------------- LN-PPV-END ------------------------
```

Next, a piece of software on the side of the client (e.g. browser extension) would find the invoice block and after successful payment decrypt (obtaing a preimage) the user is able to:
1. Obtain the data decryption key by decrypt the Description field using preimage as a key
2. Decrypt the data section of the "packet"
3. Replace the "packet" with the decrypted content

There's no need for additional server-client communication (apart from payment settlement). 

Additionaly (depending on the usecase and security concerns) content encryption key can be the same as preimage. This trick allows for the payer to "leak" the decryption key to other nodes along the route path.

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
This feature is of course not always wanted (I'd argue that it could be considered malicious in most of the cases). 

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
