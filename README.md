# QingCloud API For OpenStack

1. 依赖
    *   nova-api

2. QingCloud提供支持API列表：
    
    *  DescribeInstances
    *  RunInstances 
    *  DescribeVolumes 
    *  AttachVolumes 
    *  DescribeEips 
    *  AllocateEips      
    *  AssociateEip 
    *  DescribeImages
    
    
3. 修改nova 节点下的/etc/nova/api-paste.ini,在最后加入以下代码。
   
        [composite:qingcloud_openstack]
        use = egg:Paste#urlmap
        /v2: qingcloud_openstack_compute_api_v2

        [composite:qingcloud_openstack_compute_api_v2]
        use = call:nova.api.auth:pipeline_factory
        noauth = faultwrap sizelimit noauth ratelimit
        noauth2 = faultwrap noauth2 ratelimit
        keystone = faultwrap authtoken keystonecontext ratelimit qcapi_compute_app_v2
        keystone_nolimit = faultwrap authtoken keystonecontext qcapi_compute_app_v2


        [filter:compute_req_id]
        paste.filter_factory = nova.api.compute_req_id:ComputeReqIdMiddleware.factory

        [filter:faultwrap]
        paste.filter_factory = nova.api.qingcloud_openstack:FaultWrapper.factory

        [filter:noauth]
        paste.filter_factory = nova.api.qingcloud_openstack.auth:NoAuthMiddlewareOld.factory

        [filter:noauth2]
        paste.filter_factory = nova.api.qingcloud_openstack.auth:NoAuthMiddleware.factory 
   
4. 修改nova 节点下的/etc/nova/nova.conf 
       
        [DEFAULT]
        enabled_apis = ec2,osapi_compute,metadata,qingcloud_openstack
        qingcloud_openstack_listen_port = 8585
        qingcloud_openstack_listen = 0.0.0.0
        qingcloud_openstack_workers = 2
        
5. 启动nova-api-qingcloud
   如果配置在/etc/nova/nova.conf的enabled_apis参数中，直接启动nova-api就会启动nova-api-qingcloud
   单独启动nova-api-qingcloud启动即可。
    
