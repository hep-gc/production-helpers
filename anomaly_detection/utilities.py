# @AUTHOR: Victor Kamel

# IO
import io
import sys
import shlex
# Hashing
from hashlib import md5
# Email
import imghdr
import smtplib
from email.message import EmailMessage

class Progress:
    """
    Simple progress logging class. Use with a 'with' statement.
    
    >>> with Progress("Working..."):
    ...     print("Sample output")
    ... 
    [Info] Working...
    Sample output
    [Done]
    """
    
    def __init__(self, message, status="Info"):
        """
        Initialize.
        """
        self.msg = message if status is None else f"[{status}] " + message
        
    def __enter__(self):
        print(self.msg, flush=True)
        
    def __exit__(self, type, value, traceback):
        print("[Done]", flush=True, end="\n")

def load_config(path):
    """
    Load configuration file / host manifest.
    """
    config, manifest = {}, []
    with open(path, 'r') as file:
        mode = 0 # 0 = None, 1 = Manifest, 2 = Config
        for line in file.readlines():
            line = shlex.split(line, comments='#')
            # print(line)
            if any(line):
                if   line == ["[manifest]"]  : mode = 1
                elif line == ["[config]"]: mode = 2
                elif mode == 1:
                    if len(line) == 3:
                        manifest.append(line[:-1] + [line[-1].split(',')])
                    elif len(line) == 5:
                        manifest.append(line[:2] + [line[2].split(',')] + line[3:])
                elif mode == 2: config[line[0]] = line[1]
                else: raise Exception("Unknown value encountered while parsing config file: " + str(line))
    
    return config, manifest

def hash_objects(*args): return md5(''.join(map(str, args)).encode()).hexdigest() # Hash all arguments provided as strings

def send_report(subj, from_, to_, message, anomalous_hosts):
    """
    Send an anomaly report by email.
    
    from_ :          Sender 
    to_ :            Recipient(s)
    message:         Message to send (plain text)
    anomalous_hosts: List of hostnames of anomalous hosts
    """

    # Create the container email message
    msg = EmailMessage()
    msg['Subject'], msg['From'], msg['To'] = subj, from_, to_

    # Add text 
    msg.set_content(message)
    msg.add_alternative(f"<pre>{message}</pre>", subtype='html')

    # Add images
    for host in anomalous_hosts:
        with open(f"output/{host[1]}.png", 'rb') as fp: img_data = fp.read()
        msg.add_attachment(img_data, maintype='image', subtype=imghdr.what(None, img_data), filename=f'{host[1]}.png')

    # Send the email
    with smtplib.SMTP('localhost') as s: s.send_message(msg)