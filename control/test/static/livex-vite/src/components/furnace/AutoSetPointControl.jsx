import { checkNull } from '../../utils';

import React from "react";
import { TitleCard, WithEndpoint } from 'odin-react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';

import FloatingLabel from 'react-bootstrap/FloatingLabel';
import { floatingInputStyle, floatingLabelStyle } from '../../utils';

const EndPointButton = WithEndpoint(Button);
const EndpointSelect = WithEndpoint(Form.Select);
const EndPointFormControl = WithEndpoint(Form.Control);

function AutoSetPointControl(props){
    const {furnaceEndPoint} = props;
    const {connectedPuttingDisable} = props;

    return (
        <TitleCard
          title={
            <Row>
              <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Auto Set Point Control</Col>
              <Col xs={3}>
                <EndPointButton
                  endpoint={furnaceEndPoint}
                  fullpath="autosp/enable"
                  value={furnaceEndPoint.data.autosp?.enable ? false : true}
                  variant={furnaceEndPoint.data.autosp?.enable ? 'danger' : 'primary'}
                  >
                    {furnaceEndPoint.data.autosp?.enable ? "Disable" : "Enable"}
                </EndPointButton>
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
                  buttonText={furnaceEndPoint.data.autosp?.heating_options[furnaceEndPoint.data.autosp.heating] || "Unknown"}
                  style={floatingInputStyle}
                  disabled={connectedPuttingDisable}>
                      {furnaceEndPoint.data.autosp?.heating_options ? (
                        furnaceEndPoint.data.autosp.heating_options.map((label, index) => (
                          <option value={index} key={index}>
                            {label}
                          </option>
                        ))
                      ) : (
                        <></>
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