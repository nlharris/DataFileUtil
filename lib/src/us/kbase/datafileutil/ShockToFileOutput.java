
package us.kbase.datafileutil;

import java.util.HashMap;
import java.util.Map;
import javax.annotation.Generated;
import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonPropertyOrder;


/**
 * <p>Original spec-file type: ShockToFileOutput</p>
 * 
 * 
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@Generated("com.googlecode.jsonschema2pojo")
@JsonPropertyOrder({
    "node_file_name",
    "attributes"
})
public class ShockToFileOutput {

    @JsonProperty("node_file_name")
    private java.lang.String nodeFileName;
    @JsonProperty("attributes")
    private Map<String, String> attributes;
    private Map<java.lang.String, Object> additionalProperties = new HashMap<java.lang.String, Object>();

    @JsonProperty("node_file_name")
    public java.lang.String getNodeFileName() {
        return nodeFileName;
    }

    @JsonProperty("node_file_name")
    public void setNodeFileName(java.lang.String nodeFileName) {
        this.nodeFileName = nodeFileName;
    }

    public ShockToFileOutput withNodeFileName(java.lang.String nodeFileName) {
        this.nodeFileName = nodeFileName;
        return this;
    }

    @JsonProperty("attributes")
    public Map<String, String> getAttributes() {
        return attributes;
    }

    @JsonProperty("attributes")
    public void setAttributes(Map<String, String> attributes) {
        this.attributes = attributes;
    }

    public ShockToFileOutput withAttributes(Map<String, String> attributes) {
        this.attributes = attributes;
        return this;
    }

    @JsonAnyGetter
    public Map<java.lang.String, Object> getAdditionalProperties() {
        return this.additionalProperties;
    }

    @JsonAnySetter
    public void setAdditionalProperties(java.lang.String name, Object value) {
        this.additionalProperties.put(name, value);
    }

    @Override
    public java.lang.String toString() {
        return ((((((("ShockToFileOutput"+" [nodeFileName=")+ nodeFileName)+", attributes=")+ attributes)+", additionalProperties=")+ additionalProperties)+"]");
    }

}
