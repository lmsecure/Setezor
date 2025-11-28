from setezor.tools.ip_tools import get_network
from setezor.models import ASN, Network, IP



class IpInfoParser:

    @classmethod
    def restruct_result(cls, target: str, data: dict):

        # data:
        #   status	        string      success or fail	                                                                                                success
        # 	message	        string      included only when status is fail Can be one of the following:                                                  private range, reserved range, invalid query	invalid query
        # 	continent	    string      Continent name	                                                                                                North America
        # 	continentCode   string	    Two-letter continent code	                                                                                    NA
        # 	country	        string      Country name	                                                                                                United States
        # 	countryCode     string      Two-letter country code ISO 3166-1 alpha-2	                                                                    US
        # 	region	        string      Region/state short code (FIPS or ISO)	                                                                        CA or 10
        # 	regionName	    string      Region/state	                                                                                                California
        # 	city	        string      City                                                                                                            Mountain View
        # 	district	    string      District (subdivision of city)	                                                                                Old Farm District
        # 	zip	            string      Zip code	                                                                                                    94043
        # 	lat	            float       Latitude	                                                                                                    37.4192
        # 	lon	            float       Longitude	                                                                                                    -122.0574
        # 	timezone	    string      Timezone (tz)	                                                                                                America/Los_Angeles
        # 	offset	        int         Timezone UTC DST offset in seconds	                                                                            -25200
        # 	currency	    string      National currency	                                                                                            USD
        # 	isp	            string      ISP name	                                                                                                    Google
        # 	org	            string      Organization name	                                                                                            Google
        # 	as	            string      AS number and organization, separated by space (RIR). Empty for IP blocks not being announced in BGP tables.    AS15169 Google Inc.
        # 	asname	        string      AS name (RIR). Empty for IP blocks not being announced in BGP tables.	                                        GOOGLE
        # 	reverse	        string      Reverse DNS of the IP (can delay response)	                                                                    wi-in-f94.1e100.net
        # 	mobile	        bool        Mobile (cellular) connection	                                                                                true
        # 	proxy	        bool        Proxy, VPN or Tor exit address	                                                                                true
        # 	hosting	        bool        Hosting, colocated or data center	                                                                            true
        # 	query	        string      IP used for the query	                                                                                        173.194.67.94

        result = []
        asn_obj: ASN = ASN(
            name=data.get("asname"),
            number=data.get("as", "").split()[0],
            org=data.get("org"),
            isp=data.get("isp"),
            hosting=data.get("hosting"),
            proxy=data.get("proxy"),
            country=data.get("country"),
            city=data.get("city"),
        )
        result.append(asn_obj)
        start_ip, broadcast = get_network(ip=target, mask=24)
        network_obj = Network(start_ip=start_ip, asn=asn_obj, mask=24)
        result.append(network_obj)
        ip_obj = IP(ip=target, network=network_obj)
        result.append(ip_obj)

        return result
