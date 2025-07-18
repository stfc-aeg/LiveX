import React from 'react';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import Dropdown from 'react-bootstrap/Dropdown';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/esm/Col';
import { Container } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import { TitleCard, WithEndpoint, useAdapterEndpoint } from 'odin-react';
import DropdownSelector from '../DropdownSelector.jsx';
import TagInput from "./TagInput";

const EndPointFormControl = WithEndpoint(Form.Control);
const EndpointDropdown = WithEndpoint(DropdownSelector);
const EndpointButton = WithEndpoint(Button);

function Metadata(props) {

    const {endpoint_url} = props;

    const metadataEndPoint = useAdapterEndpoint('metadata', endpoint_url, 5000);
    // Need some object defined even when metadataEndPoint is resolving to null
    const metaJson = metadataEndPoint?.data?.fields ? metadataEndPoint.data.fields : {} ;

    const [labelWidth, setLabelWidth] = useState("60px"); // Default value if metaJson is not updated

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
          // console.log("label:", fields[key].label)
          if (labelLength > maxLength && valid) {
            maxLength = labelLength;
          }
        });
        const additionalPadding = 24; // Extra room for borders
        return `${maxLength * 10 + additionalPadding}px`;
      };

      const calculatedWidth = calculateLabelWidth(metaJson);
      setLabelWidth(calculatedWidth);
    }
  }, [metaJson]); // Only re-run the effect if metaJson changes


    const renderForm = () => {
        return Object.keys(metaJson).map((key) => {
            const field = metaJson[key];
            const {label, choices, user_input, multi_line, multi_choice=false} = field;

            const currentValue = metadataEndPoint?.data?.fields?.[key]?.value;

            // Carving out a specific exception for this non-user-input for now
            if (["acquisition_num", "start_time", "stop_time"].includes(key))
            {
              // Label is split on the parentheses of acquisition number
              // until more refined solution (metadata field property) is introduced
              return (
                <InputGroup>
                  <InputGroup.Text style={{width:labelWidth}}>
                    {label.split('(')[0]} 
                  </InputGroup.Text>
                  <InputGroup.Text>
                      {currentValue}
                    </InputGroup.Text>
                  {key=='acquisition_num' ?
                  <Col>
                    <EndpointButton
                      endpoint={metadataEndPoint}
                      fullpath={"fields/"+key+"/value"}
                      value={currentValue+1}
                      event_type="click"
                      variant="outline-secondary"
                    >
                      +
                    </EndpointButton>
                    <EndpointButton
                      endpoint={metadataEndPoint}
                      fullpath={"fields/"+key+"/value"}
                      value={currentValue-1}
                      event_type="click"
                      variant="outline-secondary"
                    >
                      -
                    </EndpointButton>
                  </Col>
                    :
                    <></>
                }

                </InputGroup>
              )
            }
            if (!user_input) {
                return null; // Skip non-user-input fields
            }

            if (choices && multi_choice === true)
            { // Tags
              return (
                <TagInput
                  options={metadataEndPoint?.data?.fields[key]?.choices}
                  metadataEndPoint={metadataEndPoint}
                  field={key}
                  labelWidth={labelWidth}
                  key={key}
                  currentValue={currentValue}
                />
              )
            }
            else if (choices)
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
                      buttonText={currentValue}>
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
                    event_type="enter"
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
                  event_type="enter">
                </EndPointFormControl>
              </InputGroup>
              )
            }
        })
    }
return(
  <Container>
    <TitleCard title="Experiment Details">
        {renderForm()}
    </TitleCard>
  </Container>
    )
}

export default Metadata;

