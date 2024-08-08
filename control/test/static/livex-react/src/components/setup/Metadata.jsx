import React from 'react';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import Dropdown from 'react-bootstrap/Dropdown';
import { useState, useEffect } from 'react';
import { TitleCard, WithEndpoint, useAdapterEndpoint, DropdownSelector } from 'odin-react';
import TagInput from "./TagInput";

const EndPointFormControl = WithEndpoint(Form.Control);
const EndpointDropdown = WithEndpoint(DropdownSelector);

function Metadata(props) {

    const {endpoint_url} = props;

    const metadataEndPoint = useAdapterEndpoint('metadata', endpoint_url, 5000);
    // Need some object defined even when metadataEndPoint is resolving to null
    const metaJson = metadataEndPoint?.data?.fields ? metadataEndPoint.data.fields : {} ;

    const [labelWidth, setLabelWidth] = useState("40px"); // Default value if metaJson is not updated

    // Calculate a 'minimum' label width to make the inputgroup.texts consistent
    useEffect(() => {
    // No need to calculate if there's no keys (i.e.: endpoint not found)
    if (Object.keys(metaJson).length > 0) {

      // Function to calculate width
      const calculateLabelWidth = (fields) => {
        let maxLength = 0;
        Object.keys(fields).forEach((key) => {
          const labelLength = fields[key].label.length;
          const valid = fields[key].user_input;
          console.log("label:", fields[key].label)
          if (labelLength > maxLength && valid) {
            maxLength = labelLength;
          }
        });
        const additionalPadding = 24; // Extra room for borders
        return `${maxLength * 6 + additionalPadding}px`;
      };

      const calculatedWidth = calculateLabelWidth(metaJson);
      setLabelWidth(calculatedWidth);
    }
  }, [metaJson]); // Only re-run the effect if metaJson changes


    const renderForm = () => {
        return Object.keys(metaJson).map((key) => {
            const field = metaJson[key];
            const {label, choices, default: defaultValue, multi_choice, user_input, multi_line, enabled} = field;

            if (!user_input) {
                return null; // Skip non-user-input fields
            }

            if (choices && !multi_choice)
            { // Dropdown
              return (
                <InputGroup>
                  <InputGroup.Text style={{width:labelWidth}}>
                    {label}:
                  </InputGroup.Text>
                  <EndpointDropdown
                  endpoint={metadataEndPoint}
                  event_type="select"
                  fullpath={"fields/"+key+"/value"}
                  variant="outline-secondary"
                  buttonText={metadataEndPoint?.data?.fields?.[key]?.value}>
                    {choices.map(
                    (selection, index) => (
                      <Dropdown.Item
                        eventKey={selection}
                        key={index}>
                          {selection}
                      </Dropdown.Item>
                    ))}
                  </EndpointDropdown>
                </InputGroup>
                )
            }
            else if (choices && multi_choice)
            { // Tags
              return (
                <TagInput
                  options={metadataEndPoint?.data?.fields[key]?.choices}
                  metadataEndPoint={metadataEndPoint}
                  field={key}
                  labelWidth={labelWidth}
                  key={key}
                />
              )
            }
            else if (multi_line)
            {  // not dropdown or tags, so text. but multi_line, not regular
              return (
                <InputGroup
                  style={{
                    display: 'flex',
                    width: '100%'
                    }}>
                  <InputGroup.Text style={{width:labelWidth}}>
                    {label}:
                  </InputGroup.Text>
                  <EndPointFormControl
                    endpoint={metadataEndPoint}
                    type="text"
                    fullpath={"fields/"+key+"/value"}
                    value={defaultValue}
                    as="textarea"
                    rows="5"
                    style={{flex: 1}}>
                </EndPointFormControl>
                </InputGroup>
              )
            }
            else
            { // Everything that's not a dropdown, tag, or large box, is a normal text field
              return (
              <InputGroup>
                <InputGroup.Text style={{width:labelWidth}}>
                  {label}:
                </InputGroup.Text>
                <EndPointFormControl
                  endpoint={metadataEndPoint}
                  type="text"
                  fullpath={"fields/"+key+"/value"}
                  value={defaultValue}>
                </EndPointFormControl>
              </InputGroup>
              )
            }
        })
    }
return(

    <TitleCard title="Experiment Details">
        {renderForm()}
    </TitleCard>
    )
}

export default Metadata;

