import React from 'react';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import { TitleCard, WithEndpoint } from 'odin-react';
import ToggleSwitch from '../ToggleSwitch';
import { checkNull  } from '../../utils';

import { floatingInputStyle, floatingLabelStyle } from '../../utils';
import { FloatingLabel } from 'react-bootstrap';


const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointToggle = WithEndpoint(ToggleSwitch);

function PidControl(props) {
    const {furnaceEndPoint} = props;
    const {connectedPuttingDisable} = props;
    const {title} = props;
    const {pid} = props;

    const labelWidth="100px";

    return (
      <TitleCard
        title={
          <Row>
            <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>{title}</Col>
            <Col xs={3}>
              <EndPointToggle
                endpoint={furnaceEndPoint}
                fullpath={pid+"/enable"}
                event_type="click"
                checked={furnaceEndPoint.data[pid]?.enable || false}
                label="Enable"
                disabled={connectedPuttingDisable}>
              </EndPointToggle>
            </Col>
          </Row>
        }>
        <Row>
          <Col>
            <Row>
              <Col xs={6}>
                <Row>
                  <FloatingLabel
                    label="Proportional">
                      <EndPointFormControl
                        endpoint={furnaceEndPoint}
                        type="number"
                        fullpath={pid+"/proportional"}
                        disabled={connectedPuttingDisable}
                        style={floatingInputStyle}
                      />
                  </FloatingLabel>
                   <FloatingLabel
                    label="Integral">
                      <EndPointFormControl
                        endpoint={furnaceEndPoint}
                        type="number"
                        fullpath={pid+"/integral"}
                        disabled={connectedPuttingDisable}
                        style={floatingInputStyle}
                      />
                  </FloatingLabel>
                  <FloatingLabel
                    label="Derivative">
                      <EndPointFormControl
                        endpoint={furnaceEndPoint}
                        type="number"
                        fullpath={pid+"/derivative"}
                        disabled={connectedPuttingDisable}
                        style={floatingInputStyle}
                      />
                  </FloatingLabel>
                </Row>
              </Col>
              <Col xs={6}>
                <Row>
                  <FloatingLabel
                    label="Enter set pt.">
                      <EndPointFormControl
                        endpoint={furnaceEndPoint}
                        type="number"
                        fullpath={pid+"/setpoint"}
                        disabled={connectedPuttingDisable}
                        style={floatingInputStyle}
                      />
                  </FloatingLabel>
                  <FloatingLabel
                    label="Current set pt.">
                      <Form.Control
                        plaintext
                        readOnly
                        style={floatingLabelStyle}
                        value={checkNull(furnaceEndPoint.data[pid]?.setpoint)}
                      />
                  </FloatingLabel>
                </Row>
                <Row>
                  <Col xs={8} sm={6}>
                    <FloatingLabel
                      label="Temperature">
                        <Form.Control
                          plaintext
                          readOnly
                          style={{
                              width: "100%",
                              border: '1px solid lightblue',
                              backgroundColor: '#e0f7ff',
                              borderRadius: '0.375rem'
                          }}

                          value={checkNull((furnaceEndPoint.data[pid]?.temperature))}
                        />
                    </FloatingLabel>
                  </Col>
                  <Col xs={8} sm={6}>
                    <FloatingLabel
                      label="Set/target diff.">
                        <Form.Control
                          plaintext
                          readOnly
                          style={{
                              width: "100%",
                              border: '1px solid lightblue',
                              backgroundColor: '#e0f7ff',
                              borderRadius: '0.375rem'
                          }}

                          value={
                            Math.abs(
                              checkNull((furnaceEndPoint.data[pid]?.setpoint)) -
                              checkNull((furnaceEndPoint.data[pid]?.temperature))
                            )
                          }
                        />
                    </FloatingLabel>
                  </Col>
                </Row>
              </Col>
            </Row>
          </Col>
        </Row>
      </TitleCard>
    )
}

export default PidControl;