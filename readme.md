# maven downloader py3


# usage

```
python3 maven_downloader.py -l com.huawei.hms:push -u https://developer.huawei.com/repo/
python3 maven_downloader.py -l com.alibaba:fastjson:1.2.73 -u http://mirrors.cloud.tencent.com/nexus/repository/maven-public/

➜  maven_downloader git:(master) ✗ tree com*
com.huawei.agconnect
└── agconnect-core
    └── agconnect-core-1.4.0.300.aar
com.huawei.hmf
└── tasks
    ├── tasks-1.3.3.300.aar
    └── tasks-1.4.1.300.aar
com.huawei.hms
├── availableupdate
│   └── availableupdate-5.0.0.301.aar
├── base
│   └── base-5.0.0.301.aar
├── device
│   └── device-5.0.0.301.aar
├── log
│   └── log-5.0.0.301.aar
├── network-common
│   └── network-common-4.0.2.300.aar
├── network-grs
│   └── network-grs-4.0.2.300.aar
├── opendevice
│   └── opendevice-5.0.0.301.aar
├── push
│   └── push-5.0.1.300.aar
├── stats
│   └── stats-5.0.0.301.aar
├── ui
│   └── ui-5.0.0.301.aar
└── update
    └── update-2.0.6.302.aar

```

参考链接：https://github.com/ochinchina/maven-downloader-py/blob/master/maven-downloader.py
