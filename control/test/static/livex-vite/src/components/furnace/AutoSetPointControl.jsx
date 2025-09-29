import { checkNull } from '../../utils';

import React from "react";
import { TitleCard, WithEndpoint } from 'odin-react';
import ToggleSwitch from '../ToggleSwitch';
import DropdownSelector from '../DropdownSelector';
import InputGroup from 'react-bootstrap/InputGroup';
import Form from 'react-bootstrap/Form';
import Dropdown from 'react-bootstrap/Dropdown';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';

import FloatingLabel from 'react-bootstrap/FloatingLabel';
import { floatingInputStyle, floatingLabelStyle } from '../../utils';

const EndpointDropdown = WithEndpoint(DropdownSelector);
const EndpointSelect = WithEndpoint(Form.Select);
const EndPointToggle = WithEndpoint(ToggleSwitch);
const EndPointFormControl = WithEndpoint(Form.Control);

function AutoSetPointControl(props){
    const {furnaceEndPoint} = props;
    const {connectedPuttingDisable} = props;

    const heating_metadata = furnaceEndPoint.metadata.autosp?.heating;

    return (
        <TitleCard
          title={
            <Row>
              <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Auto Set Point Control</Col>
              <Col xs={3}>
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
          }>
          <Row>
            <Col xs={6} sm={4}>
              <FloatingLabel
              label="Rate (K/s)">
                <EndPointFormControl
                  endpoint={furnaceEndPoint}
                  type="number"
                  fullpath="autosp/rate"
                  event_type="enter"
                  disabled={connectedPuttingDisable}
                  style={floatingInputStyle}>
                </EndPointFormControl>
              </FloatingLabel>
            </Col>
            <Col xs={6} sm={4}>
            <FloatingLabel
              label="Heat/Cool:">
                <EndpointSelect
                  endpoint={furnaceEndPoint}
                  fullpath="autosp/heating"
                  variant='outline-secondary'
                  buttonText={furnaceEndPoint.data.autosp?.heating}
                  style={floatingInputStyle}
                  disabled={connectedPuttingDisable}>
                    {(heating_metadata.allowed_values).map(
                      (selection, index) => (
                        <option value={selection} key={index}>
                          {selection}
                        </option>
                      )
                    )}
                </EndpointSelect>
            </FloatingLabel>
            </Col>
            <Col xs={6} sm={4}>
              <FloatingLabel
              label="Midpt. temp">
                <Form.Control
                  plaintext
                  readOnly
                  style={floatingLabelStyle}
                  value={checkNull(furnaceEndPoint.data.autosp?.midpt_temp)}
                  />
              </FloatingLabel>

            </Col>
          </Row>
      </TitleCard>
    )
}

export default AutoSetPointControl;