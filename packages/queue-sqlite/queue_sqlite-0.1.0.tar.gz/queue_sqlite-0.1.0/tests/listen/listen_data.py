from queue_sqlite.mounter.listen_mounter import ListenMounter

@ListenMounter.listener()
def key_1(data):
    print(data)