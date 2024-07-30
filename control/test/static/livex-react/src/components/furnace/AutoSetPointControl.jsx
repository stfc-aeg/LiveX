import { checkNull } from '../../utils';

import React from "react";
import { TitleCard, ToggleSwitch, DropdownSelector, StatusBox, WithEndpoint } from 'odin-react';
import InputGroup from 'react-bootstrap/InputGroup';
import Form from 'react-bootstrap/Form';
import Dropdown from 'react-bootstrap/Dropdown';
import Container from 'react-bootstrap/Container';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';

const EndpointDropdown = WithEndpoint(DropdownSelector);
const EndPointToggle = WithEndpoint(ToggleSwitch);
const EndPointFormControl = WithEndpoint(Form.Control);

function AutoSetPointControl(props){
    const {furnaceEndPoint} = props;
    const {connectedPuttingDisable} = props;

    return (
        <TitleCard title="Auto Set Point Control">
        <Container>
          <Row>
            <Col>
              <EndPointToggle
                endpoint={furnaceEndPoint}
                fullpath="autosp/enable"
                event_type="click" 
                checked={furnaceEndPoint.data.autosp?.enable || false}
                label="Enable"
                disabled={connectedPuttingDisable}>
              </EndPointToggle>
            </Col>
          </Row>
          <Row>
            <Col>
              <StatusBox
                type="info"
                label="Mid Pt. TEMP.">
                  {checkNull(furnaceEndPoint.data.autosp?.midpt_temp)}
              </StatusBox>
            </Col>
            <Col>
            <InputGroup>
              <InputGroup.Text>Heating/Cooling:</InputGroup.Text>
              <EndpointDropdown
                endpoint={furnaceEndPoint} event_type="select"
                fullpath="autosp/heating"
                variant='outline-secondary'
                buttonText={furnaceEndPoint.data.autosp?.heating_options[furnaceEndPoint.data.autosp.heating] || "Unknown"} disabled={connectedPuttingDisable}>
                {furnaceEndPoint.data.autosp?.heating_options ? furnaceEndPoint.data.autosp.heating_options.map(
                (selection, index) => (
                  <Dropdown.Item
                    eventKey={index}
                    key={index}>
                      {selection}
                  </Dropdown.Item>
                )) : <></> }
              </EndpointDropdown>
            </InputGroup>

            </Col>
            <Col>
              <InputGroup>
                <InputGroup.Text>
                   Rate (K/s)
                </InputGroup.Text>
                <EndPointFormControl
                  endpoint={furnaceEndPoint}
                  type="number"
                  fullpath="autosp/rate"
                  disabled={connectedPuttingDisable}>
                </EndPointFormControl>
              </InputGroup>
            </Col>
          </Row>
          <Row>
            <Col>
              <InputGroup>
                <InputGroup.Text>
                  Img Aquisition Per Degree (Img/K)
                </InputGroup.Text>
                <EndPointFormControl
                  endpoint={furnaceEndPoint}
                  type="number"
                  fullpath="autosp/img_per_degree"
                  disabled={connectedPuttingDisable}>
                </EndPointFormControl>
              </InputGroup>
            </Col>
          </Row>
        </Container>
      </TitleCard>
    )
}

export default AutoSetPointControl;