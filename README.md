![Coneptual Diagram](landserm-concept.png)

## What is LandSerM?
This acronim stands for **Local Area Network and Server Monitor**. That is the idea, thay you can easily configure/personalize triggers on events, custom logs, display storage and services monitoring, network changes and weird traffic, etc.

## How does it work?
You must configure some parameters so the daemon can now what to do. Let's say you only enabled the daemon to monitor the domain area of services. Then **the daemon starts to listen the events from the services you selected**. When there's a new event, it goes through the policy engine, the one that stablishes what to do with it.

The **policy engine** just follows instructions. It depends on the *domain area*, *event type* and a *detailed condition*: For example, if the **service was stopped without your intervention**; in case of storage domain it could be the `name` or the `mountpoint` of your partition or repository. If these 3 things are fulfilled, then it performs the actions you specify. It is important to choose one **priority**: `normal`, `moderate` or `urgent`.


The **actions** you that you can choose are: To modify a unit (for example, delete old files, restart service, block ip address), to execute any script, and to deliver the event information by push notification in your cellphone through notifiy, an OLED display and log files.

> [!NOTE]
> You can choose multiple actions to perform, it isn't limited by one.

## How should I configure it?

You can manually edit the `config.yaml` file or you can use `main.py config set <path.to.key> <value>`.